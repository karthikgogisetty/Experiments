"""Local reconstruction of PR 11533; seeded synthetic catalog, fixed nested predicate."""
import json
import random
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen


def call(method, path, body=None):
    req = Request("http://127.0.0.1:16433"+path, method=method, data=None if body is None else json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    with urlopen(req,timeout=120) as response:
        return json.load(response)


rng = random.Random(11533)
base = "/collections/nested"
version = call("GET","/")["version"]
call("PUT",base,{"vectors":{"product":{"size":768,"distance":"Cosine","on_disk":True}},
                 "quantization_config":{"scalar":{"type":"int8","always_ram":True}},
                 "optimizers_config":{"indexing_threshold":0,"default_segment_number":1}})
for start in range(0,30000,100):
    points = [{"id":i,"vector":{"product":[round(rng.uniform(-1,1),4) for _ in range(768)]},
               "payload":{"offers":[{"seller":(i+j)%6,"stock":(i*7+j)%23} for j in range(4)]}} for i in range(start,start+100)]
    call("PUT",base+"/points?wait=true",{"points":points})
call("PATCH",base,{"optimizers_config":{"indexing_threshold":1000}})
for i in range(600):
    info = call("GET",base)["result"]
    if info["indexed_vectors_count"]==30000 and info["status"]=="green":
        break
    time.sleep(1)
else:
    raise RuntimeError(str((info["indexed_vectors_count"],info["segments_count"],info["status"])))
samples = []
identical = 0
for trial in range(35):
    seller = trial%6
    filt = {"must":[{"nested":{"key":"offers","filter":{"must":[{"key":"seller","match":{"value":seller}},{"key":"stock","range":{"gte":10}}]}}}]}
    queries = [{"using":"product","query":[rng.uniform(-1,1) for _ in range(768)],"filter":filt,"limit":10,"params":{"hnsw_ef":128},"with_payload":True} for _ in range(6)]
    start=time.perf_counter()
    groups=call("POST",base+"/points/query/batch",{"searches":queries})["result"]
    elapsed=(time.perf_counter()-start)*1000
    assert len(groups)==6
    for q,g in zip(queries,groups):
        points=g["points"]
        assert len(points)==10 and all(any(o["seller"]==seller and o["stock"]>=10 for o in p["payload"]["offers"]) for p in points)
        single=call("POST",base+"/points/query",q)["result"]["points"]
        identical += int([p["id"] for p in single]==[p["id"] for p in points])
    if trial>=5:
        samples.append(elapsed)
Path(sys.argv[1]).write_text(json.dumps({"version":version,"collection":info,"samples_ms":samples,"identical_top10":identical,"single_checks":210},indent=2))
