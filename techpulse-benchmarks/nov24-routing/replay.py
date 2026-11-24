"""Usage: python3 replay.py TRACE_DIR. See trace hashes and revision in results.json."""
import hashlib
import json
import sys
from collections import OrderedDict, deque
from pathlib import Path


def replay(rows, capacity, delay, policy):
    caches = [OrderedDict() for _ in range(4)]
    pending = deque()
    uncached = [0]*4
    assigned = [0]*4
    total = 0
    for i, row in enumerate(rows):
        t = row["timestamp"]
        while pending and pending[0][0] <= t:
            _, worker, blocks = pending.popleft()
            cache = caches[worker]
            for b in blocks:
                cache[b] = None
                cache.move_to_end(b)
                if len(cache)>capacity:
                    cache.popitem(last=False)
        n = row["input_length"]
        blocks = row["hash_ids"][:n//512]
        assert len(blocks)==n//512
        hits = []
        for cache in caches:
            hits.append(next((j for j,b in enumerate(blocks) if b not in cache), len(blocks)))
        worker=i%4
        if policy=="prefix":
            worker=max(((i+j)%4 for j in range(4)),key=hits.__getitem__)
        uncached[worker]+=n-512*hits[worker]
        assigned[worker]+=1
        total+=n
        pending.append((t+delay,worker,blocks))
    assert sum(assigned)==len(rows) and 0<=sum(uncached)<=total
    return dict(input_tokens=total,uncached=uncached,requests=assigned)

out={"revision":"8cd2bd5b45c36dc7520cc28267018aa8ae0645c1","traces":{}}
for name in ("conversation","toolagent"):
    path=Path(sys.argv[1])/(name+"_trace.jsonl")
    rows=sorted(map(json.loads,path.read_bytes().splitlines()),key=lambda r:r['timestamp'])
    runs={}
    for cap in (256,1024,4096):
        for delay in (1,1000):
            runs[f"{cap}/{delay}"]={p:replay(rows,cap,delay,p) for p in ("round_robin","prefix")}
    out["traces"][name]=dict(requests=len(rows),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),runs=runs)
Path(__file__).with_name('results.json').write_text(json.dumps(out,indent=2))
for name,d in out["traces"].items():
    for setting,pair in d["runs"].items():
        a,b=pair.values()
        print(name,setting,round((1-sum(b['uncached'])/sum(a['uncached']))*100,1),b['requests'],max(a['uncached']),max(b['uncached']))
