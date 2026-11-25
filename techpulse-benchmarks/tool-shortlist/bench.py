"""Run python3 bench.py CASES LABELS (BFCL v4 multiple-choice JSONL)."""
import json
import re
import sqlite3
import sys
from pathlib import Path
from statistics import median

def read(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]
def schema(f):
    return json.dumps(f, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
def words(s):
    return re.findall(r'[a-z0-9]+',re.sub(r'([a-z])([A-Z])',r'\1 \2',s).lower())

cases=read(sys.argv[1])
answers={a['id']:a['ground_truth'] for a in read(sys.argv[2])}
catalog=sorted({schema(f) for c in cases for f in c['function']})
db=sqlite3.connect(':memory:')
db.execute('CREATE VIRTUAL TABLE docs USING fts5(name,description,parameters)')
for i,doc in enumerate(catalog):
    f=json.loads(doc)
    db.execute('INSERT INTO docs(rowid,name,description,parameters) VALUES(?,?,?,?)',(i+1,' '.join(words(f['name'])),f['description'],' '.join(f['parameters'].get('properties',{}))))
size=lambda docs: len(('['+','.join(docs)+']').encode())
rows=[]
for c in cases:
    gold=answers[c['id']]
    assert len(gold)==1 and len(gold[0])==1
    target=next(iter(gold[0]))
    original=[schema(f) for f in c['function'] if f['name']==target]
    assert len(original)==1
    q=c['question'][0][0]['content']
    match=' OR '.join('"'+w+'"' for w in sorted(set(words(q))))
    ids=[i-1 for i, in db.execute('SELECT rowid FROM docs WHERE docs MATCH ? ORDER BY bm25(docs,1,1,1),rowid',(match,))]
    ranked=[catalog[i] for i in ids]
    rank=ranked.index(original[0])+1 if original[0] in ranked else None
    rows.append(dict(case=c['id'],target=target,rank=rank,bytes={str(k):size(ranked[:k]) for k in (1,3,5,10,20)}))
result=dict(catalog=len(catalog),full_bytes=size(catalog),sqlite=sqlite3.sqlite_version,rows=rows)
Path(__file__).with_name('results.json').write_text(json.dumps(result))
print(len(rows),len(catalog),size(catalog))
for k in (1,3,5,10,20):
    print(k,sum(r['rank'] is not None and r['rank']<=k for r in rows),median(r['bytes'][str(k)] for r in rows))
