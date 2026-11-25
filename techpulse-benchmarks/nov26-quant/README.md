# Quantizing a local text-to-SQL model

I compared Q4_K_M and Q8_0 of Qwen2.5-Coder-0.5B-Instruct using the official Qwen GGUF files at revision ebb2015119c907b064c512bf053e945850b5875f. These are llama.cpp weight formats. This experiment does not compare native integer arithmetic kernels.

Each format ran twice on the same Apple A18 Pro GPU with llama.cpp b12668 and a 2,048-token context. The runner checks the server log for full layer offload. Order was Q4, Q8, Q8, Q4. Each new server received one untimed warmup, then the same ten prompts with greedy decoding and a 300-token output limit.

Each answer must be a single read-only SQLite query after stripping an optional Markdown fence. I compare its ordered result against a reference query on twelve fixtures, including an empty table, a zero-total case and seeded tables with repeated values. A task passes only if all twelve match. The fixtures are shared across tasks and the model never sees them. This is a small, handwritten suite rather than a general coding score.

Latency is wall time for the full HTTP response, including generation. The process high-water RSS is measured via macOS wait4 and includes resident CPU-side memory. It is not dedicated GPU VRAM. Model loading and warmup are excluded from response latency and included in peak RSS.

To reproduce on an Apple Silicon Mac, put the two GGUFs in one temporary directory under the names q4_k_m.gguf and q8_0.gguf. Run python3 bench.py /absolute/path/to/llama-server /absolute/path/to/models, then python3 report.py with Pillow and the macOS Arial fonts installed.

[Official model files](https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF/tree/ebb2015119c907b064c512bf053e945850b5875f) · [Raw answers and timings](results.json)
