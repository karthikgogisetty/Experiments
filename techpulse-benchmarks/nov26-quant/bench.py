"""Run: python3 bench.py LLAMA_SERVER MODEL_DIRECTORY. macOS Metal."""
import json
import random
import re
import resource
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, ProxyHandler, build_opener

root = Path(__file__).resolve().parent
server, models = map(lambda arg: Path(arg).resolve(), sys.argv[1:])
http = build_opener(ProxyHandler({}))
schema = 'CREATE TABLE sales(id INTEGER PRIMARY KEY, shop TEXT, day INTEGER, amount INTEGER);'
tasks = [
 ('daily','Return each day and its total amount, ordered by day.', 'SELECT day,sum(amount) FROM sales GROUP BY day ORDER BY day'),
 ('ties','Return id of every sale tied for highest amount within its shop. Order by id.', 'SELECT id FROM sales s WHERE amount=(SELECT max(amount) FROM sales t WHERE t.shop=s.shop) ORDER BY id'),
 ('second','Return the second highest DISTINCT amount as one row. Return no rows if fewer than two distinct amounts exist.', 'SELECT DISTINCT amount FROM sales ORDER BY amount DESC LIMIT 1 OFFSET 1'),
 ('missing','Return shops with no sales on day 2, alphabetical.', 'SELECT shop FROM sales GROUP BY shop HAVING sum(day=2)=0 ORDER BY shop'),
 ('running','Return id and cumulative amount within each shop in day then id order, including the current row. Order final rows by id.', 'SELECT id,sum(amount) OVER(PARTITION BY shop ORDER BY day,id ROWS UNBOUNDED PRECEDING) FROM sales ORDER BY id'),
 ('above','Return ids of sales strictly above their own shop average, ordered by id.', 'SELECT id FROM sales s WHERE amount>(SELECT avg(amount) FROM sales t WHERE s.shop=t.shop) ORDER BY id'),
 ('latest','Return one latest sale id per shop, breaking same-day ties by largest id. Sort output by id.', 'SELECT id FROM (SELECT id,row_number() OVER(PARTITION BY shop ORDER BY day DESC,id DESC) n FROM sales) WHERE n=1 ORDER BY id'),
 ('pairs','For each shop return its name and count of distinct days with sales, sorted by shop.', 'SELECT shop,count(DISTINCT day) FROM sales GROUP BY shop ORDER BY shop'),
 ('previous','Return id and amount minus the previous sale amount in that shop (day then id order). Use NULL for first sale. Order output by id.', 'SELECT id,amount-lag(amount) OVER(PARTITION BY shop ORDER BY day,id) FROM sales ORDER BY id'),
 ('share','Return shop and its total amount divided by the global total as a real number. Use NULL when global total is zero. Sort by shop.', 'SELECT shop,1.0*sum(amount)/(SELECT sum(amount) FROM sales) FROM sales GROUP BY shop ORDER BY shop'),
]
def score(sql, ref):
    results=[]
    for seed in range(12):
        rng=random.Random(seed)
        rows=[(i,rng.choice('abc'),rng.randint(1,4),rng.choice([-1,0,1,2,2,5])) for i in range(1,seed*2+1)]
        if seed==1: rows=[(1,'a',1,0)]
        con=sqlite3.connect(':memory:')
        try:
            con.execute(schema)
            con.executemany('INSERT INTO sales VALUES(?,?,?,?)',rows)
            expected=con.execute(ref).fetchall()
            con.execute('PRAGMA query_only=ON')
            allowed={sqlite3.SQLITE_SELECT,sqlite3.SQLITE_READ,sqlite3.SQLITE_FUNCTION}
            con.set_authorizer(lambda op,a,b,*_: sqlite3.SQLITE_OK if op in allowed and b!='load_extension' else sqlite3.SQLITE_DENY)
            con.set_progress_handler(lambda:1, 100000)
            actual=con.execute(sql).fetchmany(100)
            results.append(actual==expected)
        except sqlite3.Error:
            results.append(False)
        finally:
            con.close()
    return results

def run(fmt):
    model=models/(fmt+'.gguf')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port=sock.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    with tempfile.TemporaryFile(mode='w+') as log:
        proc=subprocess.Popen([str(server),'-m',str(model),'--host','127.0.0.1','--port',str(port),'-lv','4','-ngl','99','-c','2048','-np','1','--cache-ram','0'],stdout=log,stderr=log)
        try:
            for _ in range(240):
                if proc.poll() is not None: raise RuntimeError('startup failed')
                try:
                    with http.open(base+'/health',timeout=1): break
                except OSError: time.sleep(.2)
            log.seek(0)
            header=log.read()
            offload=re.findall(r'offloaded (\d+)/(\d+) layers to GPU',header)
            if not offload or int(offload[-1][0])<1 or offload[-1][0]!=offload[-1][1]:
                raise RuntimeError('Missing full GPU offload confirmation: '+header[-4000:])
            results=[]
            for name,question,ref in [('warmup','Return the number 1.','SELECT 1')]+tasks:
                payload=dict(messages=[dict(role='user',content='Write exactly one SQLite SELECT query. No explanation. Schema: '+schema+' Task: '+question)],temperature=0,seed=42,max_tokens=300)
                req=Request(base+'/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
                start=time.monotonic()
                with http.open(req,timeout=90) as r: reply=json.load(r)
                ms=1000*(time.monotonic()-start)
                choice=reply['choices'][0]
                answer=choice['message']['content'].strip()
                sql=re.sub(r'^\s*```(?:sql|sqlite)?\s*|\s*```\s*$','',answer,flags=re.I)
                if name!='warmup':
                    results.append(dict(task=name,answer=answer,finish=choice['finish_reason'],passed=score(sql,ref),ms=ms,tokens=reply['usage']['completion_tokens']))
        finally:
            if proc.poll() is None:
                proc.terminate()
                _,status,usage=__import__('os').wait4(proc.pid,0)
                proc.returncode=__import__('os').waitstatus_to_exitcode(status)
    return dict(format=fmt,layers=offload[-1],peak_process_bytes=usage.ru_maxrss,file_bytes=model.stat().st_size,results=results)

out=[]
for fmt in ('q4_k_m','q8_0','q8_0','q4_k_m'):
    out.append(run(fmt))
    (root/'results.json').write_text(json.dumps(out,indent=2))
    print(fmt,sum(all(r['passed']) for r in out[-1]['results']),flush=True)
