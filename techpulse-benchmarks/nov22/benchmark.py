"""Run against a fresh loopback Qdrant instance. Writes the observed samples alongside this file."""
import http.client
import json
import math
import random
import statistics
import sys
import time
import uuid
from pathlib import Path

rng = random.Random(11533)
http = http.client.HTTPConnection("127.0.0.1", 16433, timeout=60)
base = "/collections/bench_" + uuid.uuid4().hex


def call(method, path, body=None):
    http.request(method, path, json.dumps(body) if body is not None else None, {"Content-Type":"application/json"})
    response = http.getresponse()
    data = json.loads(response.read())
    if response.status >= 300:
        raise RuntimeError(data)
    return data


def vector():
    return [rng.uniform(-1, 1) for _ in range(64)]


version = call("GET","/")["version"]
call("PUT",base,{"vectors":{"product":{"size":64,"distance":"Cosine"}},"optimizers_config":{"indexing_threshold":1000,"default_segment_number":1}})
call("PUT",base+"/index?wait=true",{"field_name":"seller","field_schema":"integer"})
for start in range(0,24000,400):
    points = [{"id":i,"vector":{"product":vector()},"payload":{"seller":i%6}} for i in range(start,start+400)]
    call("PUT",base+"/points?wait=true",{"points":points})
for _ in range(120):
    info = call("GET",base)["result"]
    if info["status"]=="green" and info["indexed_vectors_count"]==24000:
        break
    time.sleep(1)
else:
    raise RuntimeError("index not ready")
samples = {"shared":[],"different":[]}
for trial in range(110):
    vectors = [vector() for _ in range(6)]
    order = list(samples)
    rng.shuffle(order)
    for case in order:
        sellers = [(trial if case=="shared" else trial+i)%6 for i in range(6)]
        queries = [{"using":"product","query":v,"filter":{"must":[{"key":"seller","match":{"value":s}}]},
                    "limit":10,"with_payload":True} for v,s in zip(vectors,sellers)]
        start = time.perf_counter_ns()
        result = call("POST",base+"/points/query/batch",{"searches":queries})["result"]
        elapsed = (time.perf_counter_ns()-start)/1e6
        assert len(result)==6
        for group,seller in zip(result,sellers):
            assert len(group["points"])==10 and all(p["payload"]["seller"]==seller for p in group["points"])
        if trial>=10:
            samples[case].append(elapsed)
summary = {k:{"median_ms":statistics.median(v),"p95_ms":sorted(v)[math.ceil(.95*len(v))-1]} for k,v in samples.items()}
output = Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name("results.json")
output.write_text(json.dumps(dict(version=version,indexed=info["indexed_vectors_count"],samples_ms=samples,summary=summary),indent=2))
print(version,info["indexed_vectors_count"],summary)
