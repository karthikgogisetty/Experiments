"""Offline SciFact reranking. Pass directory containing model.onnx, tokenizer.json,
corpus.parquet, queries.parquet and test.tsv. Requires onnxruntime 1.23.2,
tokenizers 0.22.1, duckdb 1.4.2 and numpy 2.3.5. Run with TOKENIZERS_PARALLELISM=false.
"""
import hashlib
import json
import math
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

import duckdb
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

root = Path(__file__).parent
inputs = Path(sys.argv[1])
def texts(name):
    rows = duckdb.connect().execute("select * from read_parquet(?)",[str(inputs/(name+".parquet"))])
    cols = [c[0] for c in rows.description]
    return {str(row[cols.index("_id")]):" ".join(str(row[cols.index(c)]) for c in ("title","text") if c in cols).strip() for row in rows.fetchall()}

docs, queries = texts("corpus"), texts("queries")
gold = defaultdict(set)
for line in (inputs/"test.tsv").read_text().splitlines()[1:]:
    q,d,s = line.split()
    if int(s)>0:
        gold[q].add(d)
tok = Tokenizer.from_file(str(inputs/"tokenizer.json"))
tok.enable_truncation(max_length=192)
tok.enable_padding(pad_id=0,pad_token="[PAD]")
opts=ort.SessionOptions()
opts.intra_op_num_threads=2
opts.inter_op_num_threads=1
sess=ort.InferenceSession(str(inputs/"model.onnx"),opts,providers=["CPUExecutionProvider"])
def rerank(q, candidates):
    scores=[]
    for start in range(0,len(candidates),10):
        pairs=[(q,docs[d]) for d in candidates[start:start+10]]
        items=tok.encode_batch(pairs)
        attributes={"input_ids":"ids","attention_mask":"attention_mask","token_type_ids":"type_ids"}
        feed={i.name:np.asarray([getattr(t,attributes[i.name]) for t in items],dtype=np.int64) for i in sess.get_inputs()}
        scores.extend(sess.run(None,feed)[0].reshape(-1).tolist())
    assert len(scores)==len(candidates) and np.isfinite(scores).all()
    return [d for _,d in sorted(zip(scores,candidates),key=lambda x:-x[0])]

def metrics(ranking, labels):
    hits=[i for i,d in enumerate(ranking[:10],1) if d in labels]
    dcg=sum(1/math.log2(i+1) for i in hits)
    ideal=sum(1/math.log2(i+1) for i in range(1,min(10,len(labels))+1))
    return {"ndcg10":dcg/ideal,"hit1":int(ranking[0] in labels)}

data=json.loads((root/"results.json").read_text())["details"]
assert {r["query"] for r in data}==set(gold) and len(data)==300
rng=random.Random(1123)
rng.shuffle(data)
for r in data[:3]:
    rerank(queries[r["query"]],r["ranking"])
out=[]
for r in data:
    q=r["query"]; candidates=r["ranking"]
    assert len(candidates)==len(set(candidates))==50
    row={"query":q,"bm25":metrics(candidates,gold[q])}
    depths=[10,50];rng.shuffle(depths)
    for k in depths:
        start=time.perf_counter_ns()
        ranked=rerank(queries[q],candidates[:k])
        elapsed=(time.perf_counter_ns()-start)/1e6
        row[str(k)]=dict(ms=elapsed,ranking=ranked,**metrics(ranked,gold[q]))
    out.append(row)
    if len(out)%50==0: print(len(out),flush=True)
summary={k:{field:float(np.mean([r[k][field] for r in out])) for field in ("hit1","ndcg10")} for k in ("bm25","10","50")}
for k in ("10","50"):
    summary[k]["median_ms"],summary[k]["p95_ms"]=np.percentile([r[k]["ms"] for r in out],[50,95]).tolist()
result=dict(model="cross-encoder/ms-marco-TinyBERT-L2-v2",revision="81d1926f67cb8eee2c2be17ca9f793c7c3bd20cc",hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs.iterdir() if p.suffix in (".parquet",".onnx",".tsv") or p.name=="tokenizer.json"},summary=summary,rows=out)
(root/"rerank-results.json").write_text(json.dumps(result))
print(summary)
