"""Measure two index designs on one in-memory SQLite table. No external dependencies."""
import json
import platform
import random
import sqlite3
import statistics
import time
from pathlib import Path

rng = random.Random(1122)
db = sqlite3.connect(":memory:")
db.execute("create table events(tenant int, seq int, latency int, payload text)")
db.executemany("insert into events values(?,?,?,?)",
               ((i%100,i,rng.randrange(500),"x"*240) for i in range(200000)))
plans, samples, sizes, queries = {}, {}, {}, {}
for name,cols in [("lookup","tenant,seq"),("cover","tenant,seq,latency")]:
    db.execute(f"create index {name} on events({cols})")
    query=f"select seq,latency from events indexed by {name} where tenant=? order by seq desc limit 100"
    queries[name]=query
    plans[name]=db.execute("explain query plan "+query,(0,)).fetchall()
    sizes[name]=db.execute("select sum(pgsize) from dbstat where name=?",(name,)).fetchone()[0]
    samples[name]=[]
for i in range(650):
    tenant=rng.randrange(100)
    keys=list(queries)
    rng.shuffle(keys)
    results=[]
    for k in keys:
        start=time.perf_counter_ns()
        rows=db.execute(queries[k],(tenant,)).fetchall()
        elapsed=(time.perf_counter_ns()-start)/1000
        results.append(rows)
        if i>=50:
            samples[k].append(elapsed)
    assert len(results[0])==100 and results[0]==results[1]
data=dict(sqlite=sqlite3.sqlite_version, machine=platform.machine(),plans=plans,bytes=sizes,queries=queries,
          samples_us=samples,median_us={k:statistics.median(v) for k,v in samples.items()})
Path(__file__).with_name("results.json").write_text(json.dumps(data,indent=2))
print(data["median_us"],sizes,plans)
