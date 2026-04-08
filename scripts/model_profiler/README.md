This script creates a graph of a model evaluated at the datasets described in a taxonomy.

Example execution:
```bash
python scripts/model_profiler/create_model_graph_score.py --taxonomy /bar/foo/taxonomy_001.txt --data /bar/foo/lm-eval/benchmark_output --output /bar/foo/outputs --models deepseek-ai_deepseek-coder-6.7B_instruct
```

The `lm-eval` data needs to be processed to `helm` format (`lm-eval_to_dataset.ipynb`)