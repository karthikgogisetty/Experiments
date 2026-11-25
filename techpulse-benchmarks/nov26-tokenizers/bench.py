"""Run separately with tokenizers 0.23.2 and 1.0.0rc5, passing the same GPT-2 tokenizer.json."""
import hashlib
import json
import os
import platform
import statistics
import sys
import sysconfig
import time
from pathlib import Path

os.environ["TOKENIZERS_PARALLELISM"] = "false"
from tokenizers import Tokenizer, __version__

stdlib = Path(sysconfig.get_path("stdlib"))
source = "".join((stdlib / name).read_text() for name in ("ast.py", "inspect.py", "pathlib.py", "dataclasses.py"))
chunks = [source[i:i+1024] for i in range(0, 256*1024, 1024)]
assert all(len(chunk) == 1024 for chunk in chunks)
vocab = Path(sys.argv[1])
t = Tokenizer.from_file(str(vocab))
if hasattr(t, "compile"):
    t = t.compile()

def run():
    return [encoding.ids for encoding in t.encode_batch(chunks, add_special_tokens=False)]

first_start = time.perf_counter_ns()
expected = run()
first_ms = (time.perf_counter_ns() - first_start) / 1e6
samples = []
for _ in range(15):
    start = time.perf_counter_ns()
    ids = run()
    samples.append((time.perf_counter_ns() - start) / 1e6)
    assert ids == expected

def digest(data):
    return hashlib.sha256(data).hexdigest()

print(json.dumps(dict(version=__version__, python=sys.version, host=platform.machine(),
    corpus_sha=digest("".join(chunks).encode()), vocab_sha=digest(vocab.read_bytes()),
    ids_sha=digest(json.dumps(expected).encode()), tokens=sum(map(len,expected)),
    first_ms=first_ms, elapsed_ms=samples, median_ms=statistics.median(samples))))
