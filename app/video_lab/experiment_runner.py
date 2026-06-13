"""
Video Capability Lab - Experiment Runner
实验执行器
"""

import time
import uuid
from datetime import datetime
from typing import Any

from app.video_lab.models import (
    VideoExperiment,
    VideoExperimentResult,
    VideoExperimentEvaluation,
    ExperimentStatus,
    MethodCategory,
    ProductionStepStatus,
)
from app.video_lab.method_registry import get_adapter_for_category
from app.video_lab.seed_data import get_method_by_id, get_test_case_by_id


class ExperimentRunner:
    """
    实验运行器。
    负责创建实验、执行实验、存储结果。
    """

    def __init__(self):
        self._experiments: dict[str, VideoExperiment] = {}
        self._results: dict[str, VideoExperimentResult] = {}
        self._evaluations: dict[str, VideoExperimentEvaluation] = {}

    def create_experiment(
        self,
        test_case_id: str,
        method_id: str,
        title: str,
        input_payload: dict[str, Any],
        params: dict[str, Any],
    ) -> VideoExperiment:
        """创建新实验"""
        exp_id = f"exp_{uuid.uuid4().hex[:12]}"
        experiment = VideoExperiment(
            id=exp_id,
            testCaseId=test_case_id,
            methodId=method_id,
            title=title,
            inputPayload=input_payload,
            params=params,
            status=ExperimentStatus.PENDING,
        )
        self._experiments[exp_id] = experiment
        return experiment

    def run_experiment(self, experiment_id: str) -> VideoExperimentResult:
        """执行指定实验"""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")

        experiment.status = ExperimentStatus.RUNNING
        experiment.startedAt = datetime.utcnow()

        # 获取 method 配置
        method = get_method_by_id(experiment.methodId)
        if not method:
            experiment.status = ExperimentStatus.FAILED
            experiment.errorMessage = f"Method not found: {experiment.methodId}"
            experiment.finishedAt = datetime.utcnow()
            raise ValueError(experiment.errorMessage)

        # 根据 method category 路由到对应 adapter
        adapter_fn = get_adapter_for_category(method.category)
        if not adapter_fn:
            experiment.status = ExperimentStatus.FAILED
            experiment.errorMessage = f"No adapter registered for category: {method.category.value}"
            experiment.finishedAt = datetime.utcnow()
            raise ValueError(experiment.errorMessage)

        # 调用 adapter 执行
        start = time.time()
        result = adapter_fn(
            experiment_id=experiment_id,
            test_case_id=experiment.testCaseId,
            input_payload=experiment.inputPayload,
            params=experiment.params,
        )
        elapsed_ms = int((time.time() - start) * 1000)

        # 检查结果是否包含失败的 step 或声明的失败
        has_failed_steps = _result_has_failed_steps(result)
        declares_failure = _result_declares_failure(result)

        if has_failed_steps or declares_failure:
            experiment.status = ExperimentStatus.FAILED
            experiment.errorMessage = result.rawOutput.get("status") or "Experiment completed with failed production steps"
        else:
            experiment.status = ExperimentStatus.SUCCEEDED
        experiment.finishedAt = datetime.utcnow()
        experiment.elapsedMs = elapsed_ms

        # 存储结果
        self._results[experiment_id] = result

        return result

    def get_experiment(self, experiment_id: str) -> VideoExperiment | None:
        """获取实验"""
        return self._experiments.get(experiment_id)

    def get_result(self, experiment_id: str) -> VideoExperimentResult | None:
        """获取实验结果"""
        return self._results.get(experiment_id)

    def list_experiments(self) -> list[VideoExperiment]:
        """列出所有实验"""
        return list(self._experiments.values())

    def list_results(self) -> list[VideoExperimentResult]:
        """列出所有实验结果"""
        return list(self._results.values())

    def get_experiments_by_test_case(self, test_case_id: str) -> list[VideoExperiment]:
        """按测试用例筛选实验"""
        return [e for e in self._experiments.values() if e.testCaseId == test_case_id]

    def get_result_for_experiment(self, experiment_id: str) -> VideoExperimentResult | None:
        """获取指定实验的结果"""
        return self._results.get(experiment_id)

    def save_evaluation(self, evaluation: VideoExperimentEvaluation) -> None:
        """保存实验评分"""
        self._evaluations[evaluation.experimentId] = evaluation

    def get_evaluation(self, experiment_id: str) -> VideoExperimentEvaluation | None:
        """获取实验评分"""
        return self._evaluations.get(experiment_id)


# 全局单例
_runner = ExperimentRunner()


def get_runner() -> ExperimentRunner:
    return _runner


def _result_has_failed_steps(result: VideoExperimentResult) -> bool:
    return any(step.status == ProductionStepStatus.FAILED for step in result.productionSteps)


def _result_declares_failure(result: VideoExperimentResult) -> bool:
    raw_status = result.rawOutput.get("status")
    productization = result.rawOutput.get("productizationRecommendation")
    ffmpeg_success = result.rawOutput.get("ffmpegSuccess")
    return (
        raw_status in {"failed", "ffmpeg_failed"}
        or productization == "failed"
        or ffmpeg_success is False
    )
