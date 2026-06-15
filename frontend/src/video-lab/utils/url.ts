/**
 * Shared URL utilities for Video Lab frontend.
 *
 * RUNTIME_BASE : the origin that serves static runtime assets.
 *                  Defaults to backend origin (API_BASE with /video-lab stripped).
 * RUNTIME_URL_PREFIX: the URL prefix for runtime assets (default: "/runtime").
 *                  Must match PUBLIC_RUNTIME_URL_PREFIX on the backend.
 *
 * Usage:
 *   import { resolveUrl, stripRuntimeUrlPrefix } from "../utils/url";
 *   <video src={resolveUrl(videoUrl)} />
 */

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";
const RUNTIME_BASE = import.meta.env.VITE_RUNTIME_BASE ?? API_BASE.replace(/\/video-lab$/, "");
const RUNTIME_URL_PREFIX = import.meta.env.VITE_RUNTIME_URL_PREFIX ?? "/runtime";

export { API_BASE, RUNTIME_BASE, RUNTIME_URL_PREFIX };

/**
 * Resolve a runtime URL to an absolute URL.
 * Handles: /runtime/..., /assets/..., http://..., https://..., and bare paths.
 */
export const resolveUrl = (u: string): string => {
  if (!u) return "";
  // Already absolute
  if (/^https?:\/\//.test(u)) return u;
  // Any path starting with / → prepend RUNTIME_BASE
  if (u.startsWith("/")) return `${RUNTIME_BASE}${u}`;
  return u;
};

/**
 * Strip the RUNTIME_URL_PREFIX from a URL to get the stored path.
 *
 * Handles:
 *   /runtime/video_lab/x.mp4  → video_lab/x.mp4
 *   /assets/video_lab/x.mp4   → video_lab/x.mp4
 *   http://host/runtime/x.mp4 → runtime/x.mp4
 *   runtime/x.mp4             → runtime/x.mp4
 *   (empty / null)            → ""
 */
export const stripRuntimeUrlPrefix = (u: string): string => {
  if (!u) return "";

  // Handle full URL with scheme
  let path = u;
  const m = u.match(/^https?:\/\/[^/]+(\/.*)$/);
  if (m) path = m[1];

  // Strip the configured prefix
  const prefix = RUNTIME_URL_PREFIX.replace(/\/$/, "");
  if (path.startsWith(`${prefix}/`)) return path.slice(prefix.length + 1);

  // Fallback: strip /runtime/ directly
  if (path.startsWith("/runtime/")) return path.slice("/runtime/".length);

  // Bare path without prefix
  return path.replace(/^\/+/, "");
};
