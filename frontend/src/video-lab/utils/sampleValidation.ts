/**
 * sampleValidation.ts - V1.2.1
 * 样片验证中心 — 工具函数与类型
 */

// V1.2.1: Local type duplication to avoid circular import from page component
interface SampleOutput { type: string; path: string; poster: string; audio_url: string; srt_url: string; manifest_url: string; }
interface SampleUrls { video_url: string; poster_url: string; audio_url: string; srt_url: string; manifest_url: string; }
interface Evaluation { readability: number | null; motion: number | null; visual_impact: number | null; stability: number | null; cost: number | null; notes: string; }
interface VisualJudgement { score: number; grade: string; summary: string; strengths: string[]; weaknesses: string[]; suggestions: string[]; judged_at: string; dimensions: Record<string, number>; }
export interface StyleSample {
  id: string; route_id: string; route_name: string; style_name: string; description: string;
  status: string; params: Record<string, unknown>; output: SampleOutput; urls: SampleUrls;
  evaluation: Evaluation; tags: string[]; content_preview: string; duration_sec: number; audio_duration_sec: number;
  created_at: string; visual_judgement: VisualJudgement | null;
  source?: { source_type?: string; experiment_id?: string; job_id?: string; run_id?: string; [key: string]: unknown };
  generation?: {
    visual_route?: string; visual_profile?: string; remotion_family?: string; route_preset?: string;
    aspect_ratio?: string; output_aspect_ratio?: string; target_duration?: number;
    key_point_count?: number; content_hash?: string; [key: string]: unknown;
  };
  asset_meta?: { final_video_url?: string; cover_url?: string; audio_url?: string; runtime_prefix?: string; [key: string]: unknown };
  quality_meta?: { structural_score?: number | null; visual_score?: number | null; warnings?: string[]; [key: string]: unknown };
  review_meta?: { review_status?: string; review_notes?: string; problem_tags?: string[] };
  job_run?: { jobId?: string; runId?: string; status?: string; stage?: string; progress?: number; [key: string]: unknown };
  schema_version?: string;
}

// ─── 类型 ────────────────────────────────────────────────────────────────────

/** 验证统计摘要 */
export interface SampleValidationStats {
  total: number;
  workbenchCount: number;
  comparingCount: number;
  scoredCount: number;
  approvedCount: number;
  problemCount: number;
  discardedCount: number;
  byRoute: Record<string, number>;
  byAspectRatio: Record<string, number>;
  byGenerationMode: Record<string, number>;
  bySource: Record<string, number>;
}

/** 样片验证标签 */
export interface SampleValidationTags {
  source: string;
  route: string;
  aspectRatio: string;
  generationMode: string;
  inputProfile: string;
  remotionFamily: string;
  layoutMode: string;
  voiceoverTimeline: string;
  status: string;
  hasVideo: boolean;
  hasCroppingRisk: boolean;
}

/** 差异参数表行 */
export interface DiffRow {
  field: string;
  label: string;
  values: Record<string, string>;
  allSame: boolean;
}

// ─── Workbench 识别 ──────────────────────────────────────────────────────────

export function isWorkbenchSample(sample: StyleSample): boolean {
  const tags = Array.isArray(sample?.tags) ? sample.tags : [];
  const params = (sample?.params ?? {}) as Record<string, unknown>;
  return tags.includes("workbench") || params.source === "workbench";
}

// ─── 路线标签 ────────────────────────────────────────────────────────────────

export function getWorkbenchRouteLabel(sample: StyleSample): string {
  const params = (sample?.params ?? {}) as Record<string, unknown>;
  const route = String(params.workbenchRoute || "");
  if (route === "pillow") return "Pillow 信息卡片";
  if (route === "remotion_data_news") return "Remotion Data News";
  if (route === "remotion_card_stack") return "Remotion Card Stack";
  return route || "未知 Workbench 路线";
}

// ─── 验证统计 ───────────────────────────────────────────────────────────────

export function computeValidationStats(samples: StyleSample[]): SampleValidationStats {
  const stats: SampleValidationStats = {
    total: samples.length,
    workbenchCount: 0,
    comparingCount: 0,
    scoredCount: 0,
    approvedCount: 0,
    problemCount: 0,
    discardedCount: 0,
    byRoute: {},
    byAspectRatio: {},
    byGenerationMode: {},
    bySource: {},
  };

  for (const s of samples) {
    // 来源
    const src = isWorkbenchSample(s) ? "workbench" : "gallery";
    stats.bySource[src] = (stats.bySource[src] ?? 0) + 1;
    if (src === "workbench") stats.workbenchCount++;

    // 状态
    if (s.status === "comparing") stats.comparingCount++;
    if (s.status === "approved") stats.approvedCount++;
    if (s.status === "rejected") stats.discardedCount++;
    if (s.review_meta?.review_status === "problem" || s.review_meta?.problem_tags?.includes("needs_fix")) {
      stats.problemCount++;
    }

    // 评分
    if (s.visual_judgement != null) stats.scoredCount++;

    // 路线
    const route = getSampleRoute(s);
    stats.byRoute[route] = (stats.byRoute[route] ?? 0) + 1;

    // 比例
    const ar = getSampleAspectRatioLabel(s);
    stats.byAspectRatio[ar] = (stats.byAspectRatio[ar] ?? 0) + 1;

    // 生成模式
    const gm = getSampleGenerationMode(s);
    stats.byGenerationMode[gm] = (stats.byGenerationMode[gm] ?? 0) + 1;
  }

  return stats;
}

// ─── 验证标签提取 ────────────────────────────────────────────────────────────

export function getSampleRoute(sample: StyleSample): string {
  if (isWorkbenchSample(sample)) return getWorkbenchRouteLabel(sample);
  const params = sample.params as Record<string, unknown>;
  const route = sample.route_name || sample.route_id || "";
  if (route.includes("pillow") || route.includes("frame_compose")) return "Pillow 信息卡片";
  if (route.includes("remotion") || route.includes("template_programmatic")) return "Remotion 动态模板";
  if (route.includes("asset") || route.includes("compose")) return "AI 素材氛围";
  // 从 params 推断
  if (params.workbenchRoute === "pillow") return "Pillow 信息卡片";
  if (params.workbenchRoute === "remotion_data_news") return "Remotion Data News";
  if (params.workbenchRoute === "remotion_card_stack") return "Remotion Card Stack";
  if (params.remotionFamily === "card_stack") return "Remotion Card Stack";
  if (params.remotionFamily === "data_news") return "Remotion Data News";
  return route || "—";
}

export function getSampleAspectRatioLabel(sample: StyleSample): string {
  const params = sample.params as Record<string, unknown>;
  const ar =
    sample.generation?.output_aspect_ratio ||
    sample.generation?.aspect_ratio ||
    (params.outputAspectRatio as string) ||
    (params.aspectRatio as string) ||
    "";
  if (ar.includes("9:16") || ar === "9/16") return "9:16";
  if (ar.includes("16:9") || ar === "16/9") return "16:9";
  if (ar === "1:1" || ar === "1/1") return "1:1";
  if (ar === "4:5" || ar === "4/5") return "4:5";
  return ar || "—";
}

export function getSampleGenerationMode(sample: StyleSample): string {
  const params = sample.params as Record<string, unknown>;
  const gm = (params.generationMode as string) || sample.generation?.visual_route || "";
  if (gm === "information_summary") return "信息总结";
  if (gm === "normal") return "普通";
  return gm || "—";
}

export function getSampleInputProfile(sample: StyleSample): string {
  const params = sample.params as Record<string, unknown>;
  return String(params.inputProfile || params.structureType || sample.generation?.route_preset || "—");
}

export function getSampleRemotionFamily(sample: StyleSample): string {
  const params = sample.params as Record<string, unknown>;
  const rf: string = String(
    sample.generation?.remotion_family ||
    (params.remotionFamily as string) ||
    String((params.remotionStyle as Record<string, unknown>)?.remotionFamily || "") ||
    "",
  );
  if (rf === "card_stack") return "card_stack";
  if (rf === "data_news") return "data_news";
  if (rf === "timeline_news") return "timeline_news";
  if (rf === "dashboard_brief") return "dashboard_brief";
  if (rf === "caption_story") return "caption_story";
  return rf || "—";
}

export function getSampleLayoutMode(sample: StyleSample): string {
  const params = sample.params as Record<string, unknown>;
  const lm =
    (params.aspectRatioLayoutMode as string) ||
    ((params.remotionStyle as Record<string, unknown>)?.aspectRatioLayoutMode as string) ||
    "";
  if (lm === "vertical_compact") return "竖屏紧凑 (9:16)";
  if (lm === "horizontal_balanced") return "横屏舒展 (16:9)";
  if (lm === "square_compact") return "方版 (1:1/4:5)";
  return lm || "—";
}

export function getSampleVoiceoverTimeline(sample: StyleSample): string {
  const params = sample.params as Record<string, unknown>;
  const vt = (params.voiceoverTimelineSource as string) || "";
  if (vt === "voiceover_segments") return "voiceover_segments";
  if (vt === "audio_scaled") return "audio_scaled";
  if (vt === "auto") return "auto";
  return vt || "—";
}

export function getSampleHasVideo(sample: StyleSample): boolean {
  return Boolean(sample.urls.video_url || sample.output?.path);
}

export function getSampleCroppingRisk(sample: StyleSample): boolean {
  const params = sample.params as Record<string, unknown>;
  const fitMode = params.fitMode || sample.generation?.visual_route || "";
  return fitMode === "cover";
}

// ─── 验证标签组 ─────────────────────────────────────────────────────────────

export function getValidationTags(sample: StyleSample): SampleValidationTags {
  return {
    source: isWorkbenchSample(sample) ? "Workbench" : "样片库",
    route: getSampleRoute(sample),
    aspectRatio: getSampleAspectRatioLabel(sample),
    generationMode: getSampleGenerationMode(sample),
    inputProfile: getSampleInputProfile(sample),
    remotionFamily: getSampleRemotionFamily(sample),
    layoutMode: getSampleLayoutMode(sample),
    voiceoverTimeline: getSampleVoiceoverTimeline(sample),
    status: sample.status,
    hasVideo: getSampleHasVideo(sample),
    hasCroppingRisk: getSampleCroppingRisk(sample),
  };
}

// ─── 差异参数表 ──────────────────────────────────────────────────────────────

const DIFF_FIELDS: Array<{ key: string; label: string; getValue: (s: StyleSample) => string }> = [
  { key: "id", label: "样片 ID", getValue: (s) => s.id },
  { key: "route", label: "路线", getValue: (s) => getSampleRoute(s) },
  { key: "aspectRatio", label: "比例", getValue: (s) => getSampleAspectRatioLabel(s) },
  { key: "generationMode", label: "生成模式", getValue: (s) => getSampleGenerationMode(s) },
  { key: "inputProfile", label: "输入格式", getValue: (s) => getSampleInputProfile(s) },
  { key: "remotionFamily", label: "Remotion Family", getValue: (s) => getSampleRemotionFamily(s) },
  { key: "layoutMode", label: "Layout Mode", getValue: (s) => getSampleLayoutMode(s) },
  { key: "voiceoverTimeline", label: "TTS 时间线", getValue: (s) => getSampleVoiceoverTimeline(s) },
  { key: "duration", label: "时长 (s)", getValue: (s) => String(s.duration_sec) },
  { key: "audioDuration", label: "音频时长 (s)", getValue: (s) => String(s.audio_duration_sec) },
  {
    key: "visualScore",
    label: "视觉评分",
    getValue: (s) => (s.visual_judgement ? `${s.visual_judgement.score} (${s.visual_judgement.grade})` : "—"),
  },
  {
    key: "status",
    label: "状态",
    getValue: (s) => {
      const m: Record<string, string> = { candidate: "候选中", approved: "已确认", rejected: "已放弃", comparing: "对比中" };
      return m[s.status] ?? s.status;
    },
  },
  {
    key: "cardStackPeekFrames",
    label: "Card Stack Peek",
    getValue: (s) => {
      const params = s.params as Record<string, unknown>;
      return String((params.cardStackPeekFrames as number) ?? "—");
    },
  },
  {
    key: "showDataViz",
    label: "数据可视化",
    getValue: (s) => {
      const params = s.params as Record<string, unknown>;
      return String(params.showDataViz ?? "—");
    },
  },
  {
    key: "targetDuration",
    label: "目标时长",
    getValue: (s) => {
      const params = s.params as Record<string, unknown>;
      return String(params.targetDuration ?? "—");
    },
  },
  {
    key: "keyPointCount",
    label: "关键点数",
    getValue: (s) => String(s.generation?.key_point_count ?? "—"),
  },
  {
    key: "structuralScore",
    label: "结构评分",
    getValue: (s) => String(s.quality_meta?.structural_score ?? "—"),
  },
  {
    key: "visualScoreMeta",
    label: "视觉评分 (meta)",
    getValue: (s) => String(s.quality_meta?.visual_score ?? "—"),
  },
  {
    key: "warnings",
    label: "警告",
    getValue: (s) => (s.quality_meta?.warnings?.length ? s.quality_meta.warnings.join(", ") : "—"),
  },
];

export function buildDiffTable(samples: StyleSample[]): DiffRow[] {
  return DIFF_FIELDS.map(({ key, label, getValue }) => {
    const values: Record<string, string> = {};
    for (const s of samples) {
      values[s.id] = getValue(s);
    }
    const uniqueVals = Object.values(values);
    const allSame = uniqueVals.length <= 1 || (uniqueVals.length > 0 && uniqueVals.every((v) => v === uniqueVals[0]));
    return { field: key, label, values, allSame };
  });
}

// ─── 验证报告生成 ────────────────────────────────────────────────────────────

export function buildValidationReport(
  samples: StyleSample[],
  goal?: string,
): string {
  const lines: string[] = [];
  lines.push("# 样片验证报告\n");
  if (goal) lines.push(`**验证目标**: ${goal}\n`);
  lines.push(`**生成时间**: ${new Date().toLocaleString("zh-CN")}\n`);
  lines.push(`**样片数量**: ${samples.length}\n`);
  lines.push("\n## 样片列表\n");

  for (const s of samples) {
    const tags = getValidationTags(s);
    const score = s.visual_judgement ? `${s.visual_judgement.score} (${s.visual_judgement.grade})` : "—";
    const statusMap: Record<string, string> = {
      candidate: "候选中",
      approved: "已确认",
      rejected: "已放弃",
      comparing: "对比中",
    };
    lines.push(`### ${s.style_name || s.id}`);
    lines.push(`- ID: \`${s.id}\``);
    lines.push(`- 路线: ${tags.route}`);
    lines.push(`- 比例: ${tags.aspectRatio}`);
    lines.push(`- 生成模式: ${tags.generationMode}`);
    lines.push(`- Remotion Family: ${tags.remotionFamily}`);
    lines.push(`- Layout Mode: ${tags.layoutMode}`);
    lines.push(`- 时长: ${s.duration_sec}s`);
    lines.push(`- 视觉评分: ${score}`);
    lines.push(`- 人工状态: ${statusMap[s.status] ?? s.status}`);
    lines.push(`- 视频: ${s.urls.video_url || s.output?.path || "—"}`);
    if (s.review_meta?.review_notes) lines.push(`- 备注: ${s.review_meta.review_notes}`);
    lines.push("");
  }

  lines.push("## 差异观察\n");
  lines.push("- [待填写] 信息清晰度：");
  lines.push("- [待填写] 画面匹配度：");
  lines.push("- [待填写] 节奏：");
  lines.push("- [待填写] TTS：");
  lines.push("- [待填写] 字幕：");
  lines.push("- [待填写] 是否适合发布：\n");

  lines.push("## 结论\n");
  lines.push("- 推荐样片：");
  lines.push("- 需要小修：");
  lines.push("- 淘汰：\n");

  lines.push("---\n*由 Style Gallery 验证中心生成*");
  return lines.join("\n");
}

// ─── 内容归一化（用于分组） ──────────────────────────────────────────────────

export function normalizeContentPreview(text: string): string {
  return (text || "").replace(/\s+/g, "").slice(0, 40);
}

// ─── 状态颜色 ────────────────────────────────────────────────────────────────

export const REVIEW_STATUS_LABELS: Record<string, { label: string; color: string }> = {
  candidate: { label: "候选中", color: "#f59e0b" },
  approved: { label: "已确认", color: "#10b981" },
  rejected: { label: "已放弃", color: "#ef4444" },
  comparing: { label: "对比中", color: "#3b82f6" },
};

export const SOURCE_LABELS: Record<string, { label: string; color: string }> = {
  workbench: { label: "Workbench", color: "#0f766e" },
  gallery: { label: "样片库", color: "#7c3aed" },
};
