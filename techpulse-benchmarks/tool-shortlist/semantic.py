"""Usage: python semantic.py INPUT_DIR. See SEMANTIC.md for model and dataset pins."""
import json
import os
import random
import re
import sqlite3
import sys
import time
from pathlib import Path

os.environ['VECLIB_MAXIMUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

root=Path(__file__).parent
inputs=Path(sys.argv[1])
def records(name):
    return [json.loads(line) for line in (inputs/name).read_text().splitlines()]
def schema(f):
    return json.dumps(f,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def words(s):
    return re.findall(r'[a-z0-9]+',re.sub(r'([a-z])([A-Z])',r'\1 \2',s).lower())

cases=records('cases')
labels={r['id']:next(iter(r['ground_truth'][0])) for r in records('labels')}
catalog=sorted({schema(f) for c in cases for f in c['function']})
assert (len(cases),len(catalog))==(200,480)
db=sqlite3.connect(':memory:')
db.execute('CREATE VIRTUAL TABLE docs USING fts5(name,description,parameters)')
texts=[]
for i,doc in enumerate(catalog):
    f=json.loads(doc)
    fields=[' '.join(words(f['name'])),f['description'],' '.join(f['parameters'].get('properties',{}))]
    db.execute('INSERT INTO docs(rowid,name,description,parameters) VALUES(?,?,?,?)',[i+1,*fields])
    texts.append(' '.join(fields))

tok=Tokenizer.from_file(str(inputs/'tokenizer.json'))
tok.enable_truncation(max_length=256)
cfg=ort.SessionOptions()
cfg.intra_op_num_threads=cfg.inter_op_num_threads=1
model=ort.InferenceSession(str(inputs/'model_qint8_arm64.onnx'),cfg,providers=['CPUExecutionProvider'])
def embed(text):
    ids=np.array([tok.encode(text).ids],dtype=np.int64)
    hidden=model.run(None,dict(input_ids=ids,attention_mask=np.ones_like(ids),token_type_ids=np.zeros_like(ids)))[0]
    v=hidden[0].mean(axis=0)
    return v/np.linalg.norm(v)
vectors=np.stack([embed(t) for t in texts])
def semantic(q):
    scores=np.einsum('ij,j->i',vectors,embed(q))
    assert np.isfinite(scores).all() and np.max(np.abs(scores))<1.0001
    return np.argsort(-scores,kind='stable')[:5].tolist()
def keyword(q):
    query=' OR '.join('"'+w+'"' for w in sorted(set(words(q))))
    return [i-1 for i, in db.execute('SELECT rowid FROM docs WHERE docs MATCH ? ORDER BY bm25(docs,1,1,1),rowid LIMIT 5',(query,))]

for fn in (semantic,keyword):
    fn('Find the weather forecast')
prior={r['case']:r['rank'] for r in json.loads((root/'results.json').read_text())['rows']}
rows={}
for repeat in range(3):
    shuffled=cases.copy()
    random.Random(1126+repeat).shuffle(shuffled)
    for n,c in enumerate(shuffled):
        key=c['id']
        q=c['question'][0][0]['content']
        target=catalog.index(schema(next(f for f in c['function'] if f['name']==labels[key])))
        row=rows.setdefault(key,dict(target=labels[key],keyword_ms=[],semantic_ms=[]))
        funcs=[keyword,semantic] if (n+repeat)%2 else [semantic,keyword]
        for fn in funcs:
            start=time.perf_counter_ns()
            shortlist=fn(q)
            ms=(time.perf_counter_ns()-start)/1e6
            rank=shortlist.index(target)+1 if target in shortlist else None
            field=fn.__name__+'_rank'
            assert row.setdefault(field,rank)==rank
            row[fn.__name__+'_ms'].append(ms)
        assert row['keyword_rank']==(prior[key] if (prior[key] or 999)<=5 else None)
(root/'semantic-results.json').write_text(json.dumps(rows))
for method in ('keyword','semantic'):
    times=[v for row in rows.values() for v in row[method+'_ms']]
    print(method,sum(row[method+'_rank'] is not None for row in rows.values()),np.percentile(times,[50,95]))
print('currency',rows['multiple_52'])
print('gains/losses',sum(not r['keyword_rank'] and bool(r['semantic_rank']) for r in rows.values()),sum(bool(r['keyword_rank']) and not r['semantic_rank'] for r in rows.values()))
