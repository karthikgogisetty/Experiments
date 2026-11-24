"""Usage: python3 benchmark.py scifact.zip. Python standard library only."""
import collections
import hashlib
import json
import math
import re
import sys
import zipfile
from pathlib import Path


def tokens(s):
    return re.findall(r"[a-z0-9]+", s.lower())


archive = Path(sys.argv[1])
with zipfile.ZipFile(archive) as z:
    docs = [json.loads(s) for s in z.open("scifact/corpus.jsonl")]
    questions = {str(q["_id"]):q["text"] for q in map(json.loads,z.open("scifact/queries.jsonl"))}
    gold = collections.defaultdict(set)
    for line in z.read("scifact/qrels/test.tsv").decode().splitlines()[1:]:
        q,d,s = line.split()
        if int(s)>0:
            gold[q].add(d)
postings = collections.defaultdict(list)
lengths = {}
for doc in docs:
    terms = tokens(doc["title"]+" "+doc["text"])
    did = str(doc["_id"])
    lengths[did] = len(terms)
    for word,freq in collections.Counter(terms).items():
        postings[word].append((did,freq))
avg = sum(lengths.values())/len(docs)
counts = dict.fromkeys((1,5,10,50),0)
details = []
for q, labels in sorted(gold.items()):
    scores = collections.Counter()
    for word in set(tokens(questions[q])):
        matches = postings[word]
        idf = math.log1p((len(docs)-len(matches)+.5)/(len(matches)+.5))
        for did,tf in matches:
            scores[did] += idf*tf*2.2/(tf+1.2*(.25+.75*lengths[did]/avg))
    ranked = sorted(scores,key=lambda did:(-scores[did],did))[:50]
    rank = next((i for i,did in enumerate(ranked,1) if did in labels),None)
    for k in counts:
        counts[k]+=int(rank is not None and rank<=k)
    details.append(dict(query=q,first_relevant_rank=rank,ranking=ranked))
out=dict(dataset_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),documents=len(docs),queries=len(gold),hits=counts,details=details)
assert all(labels <= lengths.keys() for labels in gold.values()) and len(gold)==300
Path(__file__).with_name("results.json").write_text(json.dumps(out))
print(len(docs),len(gold),counts)
