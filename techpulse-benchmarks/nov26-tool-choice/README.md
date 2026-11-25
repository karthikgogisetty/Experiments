# Does a tool request follow from the question?

Run llama.cpp b12668 on macOS arm64 with the ggml-org/functiongemma-270m-it-GGUF Q8_0 model at revision 2566ce14aedfc14fdd0de955ba67346425e67126. Start llama-server with --jinja -ngl 0 -t 4 -c 2048 -np 1 --host 127.0.0.1 --port 18973 and the model path. Run python3 bench.py and python3 bench.py --explicit, then python3 report.py with Pillow installed on macOS.

The outcome is a function-call proposal in the generated text. No device tools are connected. Commands require an exact function name and argument. Any attempted function call on an informational question counts as unwanted, including malformed arguments. The two conditions use greedy decoding and the same prompts. Each condition has six handwritten templates with four numeric substitutions. Counts describe these fixtures only. The unmodified model is a starting point for fine-tuning.

[Baseline generations](results.json) · [Explicit-rule generations](explicit.json)
