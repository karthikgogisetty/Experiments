"""Run: python3 serve_benchmark.py /path/to/llama-server /path/to/model.gguf"""
import contextlib
import json
import os
import random
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from statistics import median
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler

urlopen = build_opener(ProxyHandler({})).open
from math import ceil

root = Path(__file__).parent
server, model = map(lambda x: str(Path(x).resolve()), sys.argv[1:])
prefixes = [("Once upon a time " + name + " walked through the forest and found a little wooden house. ")*4 for name in ("Lily","Jack","Anna","Tom")]
rng = random.Random(2411)
batches = []
for b in range(12):
    labels = [b%4]*9 + [(b+i)%4 for i in (1,2,3)]
    rng.shuffle(labels)
    batches.append(labels)

def port():
    with socket.socket() as s:
        s.bind(("127.0.0.1",0))
        return s.getsockname()[1]

def generate(addr, prompt):
    body=dict(prompt=prompt,n_predict=8,temperature=0,cache_prompt=True,stream=True,ignore_eos=True,seed=42)
    req=Request(addr+"/completion",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
    first=None
    try:
        response=urlopen(req,timeout=30)
    except HTTPError as e:
        raise RuntimeError(e.read().decode()) from e
    with response as stream:
        for line in stream:
            if line.startswith(b'data: ') and line[6:].strip()!=b'[DONE]':
                msg=json.loads(line[6:])
                if msg.get('content') and first is None:
                    first=time.perf_counter()
    assert first is not None
    return first

def trial(policy):
    results=[]
    with contextlib.ExitStack() as stack:
        addrs=[]
        for _ in range(4):
            number=port()
            p=subprocess.Popen([server,'-m',model,'--host','127.0.0.1','--port',str(number),'-ngl','0','-t','1','-tb','1','-np','1','-c','128','--cache-ram','0'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env={"PATH":os.defpath,"HOME":"/private/tmp/tp-local-serving"})
            def stop(proc=p):
                proc.terminate()
                proc.wait(timeout=15)
            stack.callback(stop)
            addr=f"http://127.0.0.1:{number}"
            for i in range(120):
                if p.poll() is not None:
                    raise RuntimeError(f"server exited {p.returncode}")
                try:
                    with urlopen(addr+"/health",timeout=1):break
                except OSError:time.sleep(.12)
            else:
                raise RuntimeError("server readiness timeout")
            addrs.append(addr)
        pools=[stack.enter_context(ThreadPoolExecutor(1)) for _ in addrs]
        for b,labels in enumerate(batches):
            # Both policies start every burst with the same four resident prompts.
            for i in range(4):
                generate(addrs[i],prefixes[i]+" Warmup.")
            def run(i,w,start):
                dispatch=time.perf_counter()
                first=generate(addrs[w],prefixes[labels[i]]+f" Chapter {b*12+i}.")
                return dict(burst=b,request=i,worker=w,queue_ms=(dispatch-start)*1000,ttft_ms=(first-start)*1000)
            start=time.perf_counter()
            futures=[]
            for i,label in enumerate(labels):
                worker=i%4 if policy=='round_robin' else label
                futures.append(pools[worker].submit(run,i,worker,start))
            results.extend(f.result() for f in futures)
    return results

out={k:[] for k in ('round_robin','affinity')}
for policy in ('round_robin','affinity','affinity','round_robin'):
    out[policy].extend(trial(policy))
    print(policy,len(out[policy]),flush=True)
def summarize(rows):
    return {metric:{'median':median(values),'p95':sorted(values)[ceil(.95*len(values))-1]} for metric in ('queue_ms','ttft_ms') for values in [[r[metric] for r in rows]]}
summary={k:summarize(v) for k,v in out.items()}
(root/'local-serving.json').write_text(json.dumps(dict(build='b12668',model='stories15M-q4_0.gguf',summary=summary,rows=out),indent=2))
print(summary)
