// Video Capability Lab - TypeScript Types

export type MethodCategory =
  | "local_frame_compose"
  | "local_media_compose"
  | "template_programmatic_render"
  | "ai_video_direct"
  | "ai_asset_then_compose"
  | "hybrid_pipeline";

export type ImplementationStatus = "available" | "mock" | "reserved" | "not_configured";

export type ExperimentStatus = "pending" | "running" | "succeeded" | "failed" | "cancelled";

export type CostLevel = "low" | "medium" | "high" | "very_high";

export type ControlLevel = "low" | "medium" | "high";

export type StabilityLevel = "low" | "medium" | "high";

export type ProductizationLevel = "low" | "medium" | "high";

export type InputType =
  | "insight_card"
  | "article"
  | "emotional_content"
  | "product_info"
  | "image"
  | "knowledge_content";

// ─────────────────────────────────────────────
// VideoTestCase
// ─────────────────────────────────────────────
export interface VideoTestCase {
  id: string;
  name: string;
  description: string;
  inputType: InputType;
  targetDurationSec: number;
  aspectRatio: string;
  evaluationFocus: string[];
  recommendedPriority: number;
}

// ─────────────────────────────────────────────
// VideoMethod
// ─────────────────────────────────────────────
export interface VideoMethod {
  id: string;
  name: string;
  category: MethodCategory;
  description: string;
  suitableScenarios: string[];
  unsuitableScenarios: string[];
  inputRequirements: string;
  outputType: string;
  costLevel: CostLevel;
  controlLevel: ControlLevel;
  stabilityLevel: StabilityLevel;
  productizationLevel: ProductizationLevel;
  implementationStatus: ImplementationStatus;
}

// ─────────────────────────────────────────────
// VideoExperiment
// ─────────────────────────────────────────────
export interface VideoExperiment {
  id: string;
  testCaseId: string;
  methodId: string;
  title: string;
  inputPayload: Record<string, unknown>;
  params: Record<string, unknown>;
  status: ExperimentStatus;
  createdAt: string | null;
  startedAt: string | null;
  finishedAt: string | null;
  elapsedMs: number | null;
  errorMessage: string | null;
}

// ─────────────────────────────────────────────
// VideoExperimentResult
// ─────────────────────────────────────────────
export interface VideoExperimentResult {
  experimentId: string;
  videoUrl: string;
  coverUrl: string;
  assets: Record<string, unknown>;
  logs: string[];
  provider: string;
  adapter: string;
  rawOutput: Record<string, unknown>;
}

// ─────────────────────────────────────────────
// VideoEvaluation
// ─────────────────────────────────────────────
export interface VideoEvaluation {
  experimentId: string;
  visualQuality: number;
  promptFollowing: number;
  informationClarity: number;
  motionNaturalness: number;
  subjectConsistency: number;
  audioSubtitleSync: number;
  stability: number;
  costAcceptability: number;
  repairability: number;
  productizationValue: number;
}

// ─────────────────────────────────────────────
// VideoMethodAdvice
// ─────────────────────────────────────────────
export interface VideoMethodAdvice {
  scenario: string;
  recommendedMethodId: string;
  backupMethodIds: string[];
  notRecommendedMethodIds: string[];
  reasoning: string;
  productizationLevel: ProductizationLevel;
  suggestedStack: string[];
  riskNotes: string[];
  nextActions: string[];
}

// ─────────────────────────────────────────────
// API Response types
// ─────────────────────────────────────────────
export interface CreateExperimentResponse {
  experiment: VideoExperiment;
  result?: VideoExperimentResult;
  error?: string;
}

export interface ExperimentWithResult {
  experiment: VideoExperiment;
  result: VideoExperimentResult | null;
}

export interface ExperimentsByTestCaseResponse {
  testCase: VideoTestCase | null;
  experiments: ExperimentWithResult[];
}
