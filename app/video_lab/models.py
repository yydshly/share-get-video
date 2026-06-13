"""
Video Capability Lab - Core Data Models
"""

from datetime import datetime
from enum import Enum
from typing import Any


class MethodCategory(str, Enum):
    LOCAL_FRAME_COMPOSE = "local_frame_compose"
    LOCAL_MEDIA_COMPOSE = "local_media_compose"
    TEMPLATE_PROGRAMMATIC_RENDER = "template_programmatic_render"
    AI_VIDEO_DIRECT = "ai_video_direct"
    AI_ASSET_THEN_COMPOSE = "ai_asset_then_compose"
    HYBRID_PIPELINE = "hybrid_pipeline"


class ImplementationStatus(str, Enum):
    AVAILABLE = "available"
    MOCK = "mock"
    RESERVED = "reserved"
    NOT_CONFIGURED = "not_configured"


class ExperimentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CostLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ControlLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class StabilityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProductizationLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InputType(str, Enum):
    INSIGHT_CARD = "insight_card"
    ARTICLE = "article"
    EMOTIONAL_CONTENT = "emotional_content"
    PRODUCT_INFO = "product_info"
    IMAGE = "image"
    KNOWLEDGE_CONTENT = "knowledge_content"
    AI_INSIGHT_SUMMARY = "ai_insight_summary"


class ProductionStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class ArtifactType(str, Enum):
    NORMALIZED_CONTENT = "normalized_content"
    KEY_POINTS = "key_points"
    VIDEO_STRATEGY = "video_strategy"
    SCRIPT = "script"
    STORYBOARD = "storyboard"
    SUBTITLE_PLAN = "subtitle_plan"
    VOICEOVER_PLAN = "voiceover_plan"
    ASSET_PLAN = "asset_plan"
    RENDER_PLAN = "render_plan"
    VIDEO_OUTPUT = "video_output"
    COVER_IMAGE = "cover_image"
    FRAME_IMAGE = "frame_image"
    MANIFEST = "manifest"
    MOCK_VIDEO = "mock_video"
    EVALUATION = "evaluation"


# ─────────────────────────────────────────────
# VideoProductionArtifact
# ─────────────────────────────────────────────
class VideoProductionArtifact:
    def __init__(
        self,
        artifact_id: str,
        type: ArtifactType,
        title: str,
        summary: str,
        payload: dict[str, Any],
    ):
        self.id = artifact_id
        self.type = type
        self.title = title
        self.summary = summary
        self.payload = payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "summary": self.summary,
            "payload": self.payload,
        }


# ─────────────────────────────────────────────
# VideoProductionStep
# ─────────────────────────────────────────────
class VideoProductionStep:
    def __init__(
        self,
        step_id: str,
        name: str,
        description: str,
        status: ProductionStepStatus = ProductionStepStatus.PENDING,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        elapsed_ms: int | None = None,
        input_summary: str | None = None,
        output_summary: str | None = None,
        key_data: dict[str, Any] | None = None,
        logs: list[str] | None = None,
        artifacts: list[VideoProductionArtifact] | None = None,
    ):
        self.id = step_id
        self.name = name
        self.description = description
        self.status = status
        self.startedAt = started_at
        self.finishedAt = finished_at
        self.elapsedMs = elapsed_ms
        self.inputSummary = input_summary
        self.outputSummary = output_summary
        self.keyData = key_data or {}
        self.logs = logs or []
        self.artifacts = artifacts or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "startedAt": self.startedAt.isoformat() if self.startedAt else None,
            "finishedAt": self.finishedAt.isoformat() if self.finishedAt else None,
            "elapsedMs": self.elapsedMs,
            "inputSummary": self.inputSummary,
            "outputSummary": self.outputSummary,
            "keyData": self.keyData,
            "logs": self.logs,
            "artifacts": [a.to_dict() for a in self.artifacts],
        }


# ─────────────────────────────────────────────
# VideoTestCase
# ─────────────────────────────────────────────
class VideoTestCase:
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        inputType: InputType,
        targetDurationSec: int,
        aspectRatio: str,
        evaluationFocus: list[str],
        recommendedPriority: int = 1,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.inputType = inputType
        self.targetDurationSec = targetDurationSec
        self.aspectRatio = aspectRatio
        self.evaluationFocus = evaluationFocus
        self.recommendedPriority = recommendedPriority

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "inputType": self.inputType.value,
            "targetDurationSec": self.targetDurationSec,
            "aspectRatio": self.aspectRatio,
            "evaluationFocus": self.evaluationFocus,
            "recommendedPriority": self.recommendedPriority,
        }


# ─────────────────────────────────────────────
# VideoMethod
# ─────────────────────────────────────────────
class VideoMethod:
    def __init__(
        self,
        id: str,
        name: str,
        category: MethodCategory,
        description: str,
        suitableScenarios: list[str],
        unsuitableScenarios: list[str],
        inputRequirements: str,
        outputType: str,
        costLevel: CostLevel,
        controlLevel: ControlLevel,
        stabilityLevel: StabilityLevel,
        productizationLevel: ProductizationLevel,
        implementationStatus: ImplementationStatus,
    ):
        self.id = id
        self.name = name
        self.category = category
        self.description = description
        self.suitableScenarios = suitableScenarios
        self.unsuitableScenarios = unsuitableScenarios
        self.inputRequirements = inputRequirements
        self.outputType = outputType
        self.costLevel = costLevel
        self.controlLevel = controlLevel
        self.stabilityLevel = stabilityLevel
        self.productizationLevel = productizationLevel
        self.implementationStatus = implementationStatus

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "suitableScenarios": self.suitableScenarios,
            "unsuitableScenarios": self.unsuitableScenarios,
            "inputRequirements": self.inputRequirements,
            "outputType": self.outputType,
            "costLevel": self.costLevel.value,
            "controlLevel": self.controlLevel.value,
            "stabilityLevel": self.stabilityLevel.value,
            "productizationLevel": self.productizationLevel.value,
            "implementationStatus": self.implementationStatus.value,
        }


# ─────────────────────────────────────────────
# VideoExperiment
# ─────────────────────────────────────────────
class VideoExperiment:
    def __init__(
        self,
        id: str,
        testCaseId: str,
        methodId: str,
        title: str,
        inputPayload: dict[str, Any],
        params: dict[str, Any],
        status: ExperimentStatus = ExperimentStatus.PENDING,
        createdAt: datetime | None = None,
        startedAt: datetime | None = None,
        finishedAt: datetime | None = None,
        elapsedMs: int | None = None,
        errorMessage: str | None = None,
    ):
        self.id = id
        self.testCaseId = testCaseId
        self.methodId = methodId
        self.title = title
        self.inputPayload = inputPayload
        self.params = params
        self.status = status
        self.createdAt = createdAt or datetime.utcnow()
        self.startedAt = startedAt
        self.finishedAt = finishedAt
        self.elapsedMs = elapsedMs
        self.errorMessage = errorMessage

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "testCaseId": self.testCaseId,
            "methodId": self.methodId,
            "title": self.title,
            "inputPayload": self.inputPayload,
            "params": self.params,
            "status": self.status.value,
            "createdAt": self.createdAt.isoformat() if self.createdAt else None,
            "startedAt": self.startedAt.isoformat() if self.startedAt else None,
            "finishedAt": self.finishedAt.isoformat() if self.finishedAt else None,
            "elapsedMs": self.elapsedMs,
            "errorMessage": self.errorMessage,
        }


# ─────────────────────────────────────────────
# VideoExperimentResult
# ─────────────────────────────────────────────
class VideoExperimentResult:
    def __init__(
        self,
        experimentId: str,
        videoUrl: str = "",
        coverUrl: str = "",
        assets: dict[str, Any] | None = None,
        logs: list[str] | None = None,
        provider: str = "",
        adapter: str = "",
        rawOutput: dict[str, Any] | None = None,
        productionSteps: list[VideoProductionStep] | None = None,
    ):
        self.experimentId = experimentId
        self.videoUrl = videoUrl
        self.coverUrl = coverUrl
        self.assets = assets or {}
        self.logs = logs or []
        self.provider = provider
        self.adapter = adapter
        self.rawOutput = rawOutput or {}
        self.productionSteps = productionSteps or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "experimentId": self.experimentId,
            "videoUrl": self.videoUrl,
            "coverUrl": self.coverUrl,
            "assets": self.assets,
            "logs": self.logs,
            "provider": self.provider,
            "adapter": self.adapter,
            "rawOutput": self.rawOutput,
            "productionSteps": [s.to_dict() for s in self.productionSteps],
        }


# ─────────────────────────────────────────────
# VideoEvaluation
# ─────────────────────────────────────────────
class VideoEvaluation:
    def __init__(
        self,
        experimentId: str,
        visualQuality: int = 0,
        promptFollowing: int = 0,
        informationClarity: int = 0,
        motionNaturalness: int = 0,
        subjectConsistency: int = 0,
        audioSubtitleSync: int = 0,
        stability: int = 0,
        costAcceptability: int = 0,
        repairability: int = 0,
        productizationValue: int = 0,
    ):
        self.experimentId = experimentId
        self.visualQuality = visualQuality
        self.promptFollowing = promptFollowing
        self.informationClarity = informationClarity
        self.motionNaturalness = motionNaturalness
        self.subjectConsistency = subjectConsistency
        self.audioSubtitleSync = audioSubtitleSync
        self.stability = stability
        self.costAcceptability = costAcceptability
        self.repairability = repairability
        self.productizationValue = productizationValue

    def to_dict(self) -> dict[str, Any]:
        return {
            "experimentId": self.experimentId,
            "visualQuality": self.visualQuality,
            "promptFollowing": self.promptFollowing,
            "informationClarity": self.informationClarity,
            "motionNaturalness": self.motionNaturalness,
            "subjectConsistency": self.subjectConsistency,
            "audioSubtitleSync": self.audioSubtitleSync,
            "stability": self.stability,
            "costAcceptability": self.costAcceptability,
            "repairability": self.repairability,
            "productizationValue": self.productizationValue,
        }


# ─────────────────────────────────────────────
# VideoMethodAdvice
# ─────────────────────────────────────────────
class VideoMethodAdvice:
    def __init__(
        self,
        scenario: str,
        recommendedMethodId: str,
        backupMethodIds: list[str],
        notRecommendedMethodIds: list[str],
        reasoning: str,
        productizationLevel: ProductizationLevel,
        suggestedStack: list[str],
        riskNotes: list[str],
        nextActions: list[str],
    ):
        self.scenario = scenario
        self.recommendedMethodId = recommendedMethodId
        self.backupMethodIds = backupMethodIds
        self.notRecommendedMethodIds = notRecommendedMethodIds
        self.reasoning = reasoning
        self.productizationLevel = productizationLevel
        self.suggestedStack = suggestedStack
        self.riskNotes = riskNotes
        self.nextActions = nextActions

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "recommendedMethodId": self.recommendedMethodId,
            "backupMethodIds": self.backupMethodIds,
            "notRecommendedMethodIds": self.notRecommendedMethodIds,
            "reasoning": self.reasoning,
            "productizationLevel": self.productizationLevel.value,
            "suggestedStack": self.suggestedStack,
            "riskNotes": self.riskNotes,
            "nextActions": self.nextActions,
        }
