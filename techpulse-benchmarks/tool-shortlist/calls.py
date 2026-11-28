"""Usage: python hybrid.py INPUT_DIR. See SEMANTIC.md for model and dataset pins."""
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

def hybrid(q):
    picked=keyword(q)[:3]
    for tool in semantic(q):
        if tool not in picked:
            picked.append(tool)
        if len(picked)==5:
            break
    assert len(set(picked))==5
    return picked

from urllib.request import build_opener, ProxyHandler, Request
from statistics import median
from call_score import parse, matches

http=build_opener(ProxyHandler({}))
truth={r['id']:r['ground_truth'][0] for r in records('labels')}
prior=json.loads((root/'hybrid-results.json').read_text())
def adapt(value):
    if isinstance(value,dict):
        return {k:({'dict':'object','float':'number','tuple':'array','list':'array'}.get(v,v) if k=='type' and isinstance(v,str) else adapt(v)) for k,v in value.items()}
    if isinstance(value,list): return [adapt(v) for v in value]
    return value
def predict(question, ids):
    tools=[]
    lookup={}
    for i in ids:
        f=adapt(json.loads(catalog[i]))
        alias=f['name'].replace('.','__')
        # Keep duplicate schema names distinguishable.
        if alias in lookup: alias+='__variant'+str(i)
        lookup[alias]=i
        f['name']=alias
        tools.append(dict(type='function',function=f))
    payload=dict(messages=[dict(role='developer',content='You are a model that can do function calling with the following functions'),dict(role='user',content=question)],tools=tools,temperature=0,seed=42,max_tokens=192,cache_prompt=False,stop=['<start_function_response>'])
    request=Request('http://127.0.0.1:18974/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with http.open(request,timeout=60) as response:
        choice=json.load(response)['choices'][0]
    return choice,lookup

predict('What is the weather in London?',hybrid('What is the weather in London?'))
rows=[]
shuffled=cases.copy()
random.Random(1128).shuffle(shuffled)
for n,c in enumerate(shuffled):
    key=c['id']
    q=c['question'][0][0]['content']
    name=labels[key]
    target=catalog.index(schema(next(f for f in c['function'] if f['name']==name)))
    for fn in ([keyword,hybrid] if n%2==0 else [hybrid,keyword]):
        start=time.perf_counter_ns()
        ids=fn(q)
        after=time.perf_counter_ns()
        choice,lookup=predict(q,ids)
        end=time.perf_counter_ns()
        rank=ids.index(target)+1 if target in ids else None
        assert rank==prior[key][fn.__name__+'_rank']
        msg=choice['message']
        output=msg.get('content') or ''
        try:
            native=msg.get('tool_calls',[])
            if native:
                assert len(native)==1
                f=native[0]['function']
                alias,args=f['name'],json.loads(f['arguments'])
            else: alias,args=parse(output)
            selected=lookup.get(alias)
        except (ValueError,AssertionError,KeyError,IndexError):
            selected,args=None,None
        right=selected==target and choice['finish_reason']!='length'
        rows.append(dict(case=key,method=fn.__name__,rank=rank,tool_ok=right,call_ok=right and matches(args,truth[key][name]),args=args,raw=msg,finish=choice['finish_reason'],retrieval_ms=(after-start)/1e6,e2e_ms=(end-start)/1e6))
    if n%25==24: print(n+1,flush=True)
(root/'call-results.json').write_text(json.dumps(rows,ensure_ascii=False))
