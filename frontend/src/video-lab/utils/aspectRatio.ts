/**
 * aspectRatio.ts — V1.2.1.5
 * Unified aspect ratio / fit-mode utilities for sample display.
 *
 * Normalises the many possible sources of aspect ratio data in a StyleSample
 * (generation.*, asset_meta.*, params.*) and provides a safe CSS value for
 * use in aspect-ratio containers.
 */

/** Valid aspect ratio strings used in this project. */
export type AspectRatio = "9:16" | "16:9" | "1:1" | "4:5";

const VALID_RATIOS: Record<string, string> = {
  "9:16": "9:16",
  "16:9": "16:9",
  "1:1": "1:1",
  "4:5": "4:5",
};

export function normalizeAspectRatio(value?: unknown): AspectRatio {
  const raw = String(value || "").trim();
  return (VALID_RATIOS[raw] as AspectRatio) || "9:16";
}

/** Convert a normalised ratio string to a CSS aspect-ratio value. */
export function aspectRatioToCss(value?: unknown): string {
  const ratio = normalizeAspectRatio(value);
  const map: Record<string, string> = {
    "16:9": "16 / 9",
    "1:1": "1 / 1",
    "4:5": "4 / 5",
    "9:16": "9 / 16",
  };
  return map[ratio] || "9 / 16";
}

/** Resolve the display aspect ratio from a StyleSample. */
export function getSampleAspectRatio(sample?: Record<string, unknown>): AspectRatio {
  if (!sample) return "9:16";
  const g = (sample["generation"] || {}) as Record<string, unknown>;
  const a = (sample["asset_meta"] || {}) as Record<string, unknown>;
  const p = (sample["params"] || {}) as Record<string, unknown>;
  return normalizeAspectRatio(
    g["display_aspect_ratio"] ||
      g["output_aspect_ratio"] ||
      g["aspect_ratio"] ||
      a["display_aspect_ratio"] ||
      a["aspect_ratio"] ||
      p["displayAspectRatio"] ||
      p["outputAspectRatio"] ||
      p["aspectRatio"] ||
      "9:16",
  );
}

/** Resolve the output (content) aspect ratio from a StyleSample. */
export function getSampleOutputAspectRatio(sample?: Record<string, unknown>): AspectRatio {
  if (!sample) return "9:16";
  const g = (sample["generation"] || {}) as Record<string, unknown>;
  const a = (sample["asset_meta"] || {}) as Record<string, unknown>;
  const p = (sample["params"] || {}) as Record<string, unknown>;
  return normalizeAspectRatio(
    g["output_aspect_ratio"] ||
      g["aspect_ratio"] ||
      a["aspect_ratio"] ||
      p["outputAspectRatio"] ||
      p["aspectRatio"] ||
      "9:16",
  );
}

/** Resolve fit mode from a StyleSample. Defaults to "contain". */
export function getSampleFitMode(sample?: Record<string, unknown>): "contain" | "cover" {
  if (!sample) return "contain";
  const g = (sample["generation"] || {}) as Record<string, unknown>;
  const a = (sample["asset_meta"] || {}) as Record<string, unknown>;
  const p = (sample["params"] || {}) as Record<string, unknown>;
  const raw = String(
    g["fit_mode"] || a["fit_mode"] || p["fitMode"] || "contain",
  ).toLowerCase();
  return raw === "cover" ? "cover" : "contain";
}

/** Describe the cropping risk for a sample, or "" when safe. */
export function getCroppingRisk(sample?: Record<string, unknown>): string {
  if (!sample) return "";
  const output = getSampleOutputAspectRatio(sample);
  const display = getSampleAspectRatio(sample);
  const fit = getSampleFitMode(sample);
  if (output !== display && fit === "cover") {
    return `风险：${output} 视频在 ${display} 容器中使用 cover 展示，可能发生裁剪。`;
  }
  return "";
}
