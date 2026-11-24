# Qdrant batch filter benchmark

Compare the official macOS arm64 releases of Qdrant 1.20.1 and 1.20.2. Run each workload sequentially on the same machine with an unused loopback port 16433 and gRPC port 16434. Python 3.12 and the two unpacked release binaries are the runtime dependencies.

    python3 compare.py /path/to/1.20.1/qdrant /path/to/1.20.2/qdrant
    python3 compare.py /path/to/1.20.1/qdrant /path/to/1.20.2/qdrant nested
    python3 chart.py

The driver starts and stops the releases in old/new/new/old order, creates fresh temporary storage per build and disables telemetry reporting. Each workload uses the same deterministic data and query sequence across builds. The flat workload checks seller membership and records 100 warmed client round trips per condition per build.

The nested workload uses 30,000 seeded 768-dimensional cosine vectors, on-disk vector storage, scalar int8 quantization in RAM, a target of one optimized segment and one search thread. Each product has four synthetic offers. Both seller identity and minimum stock must match within a single offer. There are six queries per batch, limit 10, hnsw_ef 128. After verifying all 30,000 vectors were indexed, the driver warms five batches and times 30 more per build. Each batch is followed by six standalone queries to check ordered result IDs. The single queries are outside the timed batch window. All returned payloads must satisfy the nested predicate.

The PR describes a one-vCPU cloud test of development revisions. Our Apple Silicon host, release binaries, synthetic payload and vectors, CPU scheduling and index layout can differ. The original dataset, exact nested predicate and query vectors are unspecified in the published timing table. The comparison measures the local workload; it cannot isolate the cost of a single code change.

Raw files include each timed batch. Unit is milliseconds. Summaries pool equally sized runs, reporting the median and nearest-rank 95th percentile. Percentage latency change is 100 × (new / old − 1). Retain the individual builds when assessing variation. Source: https://github.com/qdrant/qdrant/pull/11533

## Nested results on this host

| Qdrant | Build medians (ms) | Pooled median (ms) | P95 (ms) |
| --- | --- | ---: | ---: |
| 1.20.1 | 39.60, 41.91 | 41.14 | 44.50 |
| 1.20.2 | 44.53, 46.21 | 45.77 | 51.68 |

Median latency increased 11.3%. All 840 ordered top-ten checks matched, including warm-up queries. Both releases reported two total segments and 30,000 indexed vectors. This workload did not reproduce the reported speedup.
