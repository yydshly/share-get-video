"""
style_gallery/store.py - JSONL-backed Style Sample storage
V0.3.7: Style Sample Gallery — no database, just JSONL files
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from app.video_lab.style_gallery.models import StyleSample


# ─── 路径常量 ────────────────────────────────────────────────────────────────

_RUNTIME = Path(__file__).parent.parent.parent.parent.parent / "runtime" / "style_gallery"
_RECORDS_DIR = _RUNTIME / "records"
_JSONL_PATH = _RECORDS_DIR / "style_samples.jsonl"


def _ensure_dirs() -> None:
    """确保目录存在。"""
    for sub in ("pillow", "remotion", "ai_asset", "html_motion", "records"):
        (_RUNTIME / sub).mkdir(parents=True, exist_ok=True)


# ─── 读写 ────────────────────────────────────────────────────────────────────

def _read_all() -> list[dict[str, Any]]:
    """读取所有记录（按时间倒序）。"""
    _ensure_dirs()
    if not _JSONL_PATH.exists():
        return []
    records = []
    with open(_JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _write_all(records: list[dict[str, Any]]) -> None:
    """全量覆盖写回 JSONL。"""
    _ensure_dirs()
    with open(_JSONL_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ─── CRUD ─────────────────────────────────────────────────────────────────────

def list_samples(
    route_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[StyleSample]:
    """列出样片，支持按路线和状态过滤。"""
    records = _read_all()
    results = []
    for r in records:
        if route_id and r.get("route_id") != route_id:
            continue
        if status and r.get("status") != status:
            continue
        results.append(StyleSample.from_dict(r))
    # 按时间倒序
    results.sort(key=lambda s: s.created_at, reverse=True)
    return results[:limit]


def get_sample(sample_id: str) -> StyleSample | None:
    """按 ID 查询样片。"""
    records = _read_all()
    for r in records:
        if r.get("id") == sample_id:
            return StyleSample.from_dict(r)
    return None


def save_sample(sample: StyleSample) -> StyleSample:
    """新增或更新一条样片记录（按 ID 全量覆盖）。"""
    _ensure_dirs()
    records = _read_all()
    # 查找是否已存在
    idx = next((i for i, r in enumerate(records) if r.get("id") == sample.id), -1)
    d = sample.to_dict()
    if idx >= 0:
        records[idx] = d
    else:
        records.append(d)
    _write_all(records)
    return sample


def delete_sample(sample_id: str) -> bool:
    """删除一条样片记录（保留文件，文件由调用方清理）。"""
    records = _read_all()
    before = len(records)
    records = [r for r in records if r.get("id") != sample_id]
    if len(records) == before:
        return False
    _write_all(records)
    return True


def get_output_dir(sample_id: str) -> Path:
    """获取某样片的输出目录。"""
    _ensure_dirs()
    return _RUNTIME / sample_id


def to_runtime_url(path: str) -> str:
    """将各种路径格式统一转换为 /runtime/ URL。

    支持格式：
    - /runtime/video_lab/experiments/xxx/final.mp4  → 保持不变
    - runtime/video_lab/experiments/xxx/final.mp4  → /runtime/video_lab/...
    - video_lab/experiments/xxx/final.mp4          → /runtime/video_lab/...
    - style_gallery/remotion/xxx.mp4               → /runtime/style_gallery/...
    - remotion/xxx.mp4                             → /runtime/style_gallery/...
    - /runtime/style_gallery/xxx.mp4                 → 保持不变
    """
    if not path:
        return ""
    # 已经是完整 URL
    if path.startswith("http://") or path.startswith("https://"):
        return path
    # 已经是 /runtime/ 开头，直接返回
    if path.startswith("/runtime/"):
        return path
    # runtime/xxx → /runtime/xxx
    if path.startswith("runtime/"):
        return "/" + path
    # video_lab/xxx → /runtime/video_lab/xxx
    if path.startswith("video_lab/"):
        return "/runtime/" + path
    # style_gallery/xxx → /runtime/style_gallery/xxx
    if path.startswith("style_gallery/"):
        return "/runtime/" + path
    # 其他情况（如 remotion/xxx），默认归入 style_gallery
    if path == "/" or not path:
        return ""
    return "/runtime/style_gallery/" + path


def resolve_sample_urls(sample: StyleSample) -> dict[str, str]:
    """把相对路径转换为 /runtime/ URL 前缀。"""
    out = sample.output
    return {
        "video_url": to_runtime_url(out.path) if out.path else "",
        "poster_url": to_runtime_url(out.poster) if out.poster else "",
        "audio_url": to_runtime_url(out.audio_url) if out.audio_url else "",
        "srt_url": to_runtime_url(out.srt_url) if out.srt_url else "",
        "manifest_url": to_runtime_url(out.manifest_url) if out.manifest_url else "",
    }
