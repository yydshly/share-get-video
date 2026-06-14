"""
Chain Benchmark - Runner
V0.3.4.1: Executes benchmarks across multiple complete video generation chains
"""

import uuid
from datetime import datetime
from typing import Any

from app.video_lab.routes_benchmark.chain_models import (
    ChainBenchmark,
    ChainResultData,
    ChainMetrics,
)
from app.video_lab.chains.registry import get_chain, run_chain


class ChainBenchmarkRunner:
    """In-memory chain benchmark runner."""

    def __init__(self):
        self._benchmarks: dict[str, ChainBenchmark] = {}

    def create_benchmark(
        self,
        test_case_id: str,
        title: str,
        input_payload: dict,
        common_params: dict,
        chain_ids: list[str],
    ) -> ChainBenchmark:
        benchmark_id = f"chain_bench_{uuid.uuid4().hex[:12]}"
        benchmark = ChainBenchmark(
            benchmark_id=benchmark_id,
            title=title,
            test_case_id=test_case_id,
            input_payload=input_payload,
            common_params=common_params,
            chain_ids=chain_ids,
            status="pending",
        )
        self._benchmarks[benchmark_id] = benchmark
        return benchmark

    def get_benchmark(self, benchmark_id: str) -> ChainBenchmark | None:
        return self._benchmarks.get(benchmark_id)

    def run_benchmark(self, benchmark_id: str) -> ChainBenchmark:
        """Execute a benchmark across all specified chains."""
        benchmark = self._benchmarks.get(benchmark_id)
        if not benchmark:
            raise ValueError(f"Chain benchmark not found: {benchmark_id}")

        benchmark.status = "running"
        start_time = datetime.utcnow()

        for chain_def in benchmark.chain_ids:
            chain_meta = get_chain(chain_def)
            if not chain_meta:
                # Unknown chain - add as failed
                benchmark.results.append(
                    ChainResultData(
                        chain_id=chain_def,
                        chain_name=chain_def,
                        status="failed",
                        failed_step="registry",
                        failed_reason=f"Unknown chain: {chain_def}",
                    )
                )
                continue

            experiment_id = f"chain_{chain_def}_{uuid.uuid4().hex[:8]}"

            try:
                chain_result = run_chain(
                    chain_id=chain_def,
                    experiment_id=experiment_id,
                    test_case_id=benchmark.test_case_id,
                    input_payload=benchmark.input_payload,
                    params=benchmark.common_params,
                )
                result_data = ChainResultData.from_chain_result(chain_result)
                benchmark.results.append(result_data)

            except Exception as e:
                benchmark.results.append(
                    ChainResultData(
                        chain_id=chain_def,
                        chain_name=chain_meta.name,
                        status="failed",
                        failed_step="execution",
                        failed_reason=str(e)[:200],
                    )
                )

        # Determine overall status
        if all(r.status == "succeeded" for r in benchmark.results):
            benchmark.status = "completed"
        elif all(r.status in ("manual_required", "skipped") for r in benchmark.results):
            benchmark.status = "completed"
        elif all(r.status in ("failed", "incomplete", "skipped") for r in benchmark.results):
            benchmark.status = "completed"
        else:
            benchmark.status = "partial"

        benchmark.completed_at = datetime.utcnow()
        benchmark.elapsed_ms = int(
            (benchmark.completed_at - start_time).total_seconds() * 1000
        )

        return benchmark


# Singleton instance
_chain_runner: ChainBenchmarkRunner | None = None


def get_chain_runner() -> ChainBenchmarkRunner:
    global _chain_runner
    if _chain_runner is None:
        _chain_runner = ChainBenchmarkRunner()
    return _chain_runner
