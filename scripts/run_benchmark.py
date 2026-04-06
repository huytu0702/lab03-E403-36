from __future__ import annotations

import json

from src.evaluation.benchmark_runner import run_benchmark_suite


if __name__ == "__main__":
    result = run_benchmark_suite()
    print(json.dumps(result, ensure_ascii=False, indent=2))
