/**
 * Shared URL utilities for Video Lab frontend.
 *
 * RUNTIME_BASE: the origin that serves /runtime/* static assets.
 * Defaults to the backend origin (API_BASE with /video-lab stripped).
 *
 * Usage:
 *   import { resolveUrl } from "../utils/url";
 *   <video src={resolveUrl(videoUrl)} />
 */

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/video-lab";
const RUNTIME_BASE = import.meta.env.VITE_RUNTIME_BASE ?? API_BASE.replace(/\/video-lab$/, "");

export { API_BASE, RUNTIME_BASE };

export const resolveUrl = (u: string): string =>
  u && u.startsWith("/runtime/") ? `${RUNTIME_BASE}${u}` : u;
