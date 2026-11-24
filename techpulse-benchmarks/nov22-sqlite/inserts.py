"""Compare committed batches on identically populated memory databases, one index each."""
import json
import random
import sqlite3
import statistics
import time
from pathlib import Path

seed = random.Random(1122)
insert = "insert into events values(?,?,?,?)"
def rows(start, count):
    return [(i%100,i,seed.randrange(500),"x"*240) for i in range(start,start+count)]

dbs = {}
initial = rows(0,200000)
for design, columns in [("lookup","tenant,seq"),("cover","tenant,seq,latency")]:
    db = sqlite3.connect(":memory:")
    db.execute("create table events(tenant int,seq int,latency int,payload text)")
    db.executemany(insert,initial)
    db.execute(f"create index idx on events({columns})")
    db.commit()
    dbs[design] = db
samples = {name:[] for name in dbs}
order_rng = random.Random(84)
for trial in range(220):
    batch = rows(200000+trial*100,100)
    order = list(dbs)
    order_rng.shuffle(order)
    for name in order:
        db = dbs[name]
        start = time.perf_counter_ns()
        with db:
            db.executemany(insert,batch)
        elapsed = (time.perf_counter_ns()-start)/1000
        if trial>=20:
            samples[name].append(elapsed)
assert list(dbs["lookup"].execute("select * from events where seq>=200000 order by rowid")) == list(dbs["cover"].execute("select * from events where seq>=200000 order by rowid"))
out = dict(sqlite=sqlite3.sqlite_version,batch_size=100,warmup=20,samples_us=samples,median_us={k:statistics.median(v) for k,v in samples.items()})
Path(__file__).with_name("insert-results.json").write_text(json.dumps(out,indent=2))
print(out["median_us"])
