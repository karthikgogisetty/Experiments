"""Run old/new/new/old with fresh storage, a fixed workload seed and no overlapping servers."""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

here = Path(__file__).resolve().parent
old, new = map(lambda arg: Path(arg).resolve(), sys.argv[1:3])
nested = sys.argv[3:] == ["nested"]
for i, binary in enumerate([old,new,new,old],1):
    with tempfile.TemporaryDirectory() as storage:
        env = {"HOME": storage, "PATH": os.defpath, "QDRANT__SERVICE__HOST":"127.0.0.1",
               "QDRANT__SERVICE__HTTP_PORT":"16433", "QDRANT__SERVICE__GRPC_PORT":"16434"}
        if nested:
            env["QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS"]="1"
        with open(Path(storage)/"server.log","w") as log:
            server = subprocess.Popen([binary,"--disable-telemetry"],cwd=storage,env=env,stdout=log,stderr=log)
            try:
                for _ in range(100):
                    if server.poll() is not None:
                        raise RuntimeError("server exited")
                    try:
                        with urlopen("http://127.0.0.1:16433/readyz",timeout=1) as res:
                            break
                    except OSError:
                        time.sleep(.1)
                output = here/(f"nested-{i}.json" if nested else f"run-{i}.json")
                subprocess.run([sys.executable,str(here/("nested.py" if nested else "benchmark.py")),str(output)],check=True,timeout=900)
                expected = "1.20.1" if binary==old else "1.20.2"
                assert json.loads(output.read_text())["version"]==expected
            finally:
                server.terminate()
                server.wait(timeout=30)
