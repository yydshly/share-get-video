"""
Quality Log - 评分留痕（轻量持久化，无 DB）

每次生成/评分追加一条记录到 runtime/video_lab/quality_log.jsonl，
用于跨时间/跨版本追踪每条路线的质量趋势，防止静默退化。

记录两类：
- structural: 结构层确定性质量（来自 video_quality）
- perceptual: 感知层视觉模型评分（来自 visual_judge）
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# 基于 config.RUNTIME_DIR 的绝对路径，避免依赖启动 CWD（换目录后日志读写错位）。
from app.video_lab.config import RUNTIME_DIR
LOG_PATH = RUNTIME_DIR / "video_lab" / "quality_log.jsonl"


def append_record(record: dict[str, Any]) -> dict[str, Any]:
    """追加一条质量记录（自动加时间戳）。"""
    rec = {"ts": time.time(), "isoTime": datetime.utcnow().isoformat(), **record}
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def read_records(route: str | None = None, kind: str | None = None, limit: int = 300) -> list[dict[str, Any]]:
    """读取历史记录（可按 route / kind 过滤），返回最近 limit 条。"""
    if not LOG_PATH.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if route and rec.get("route") != route:
            continue
        if kind and rec.get("kind") != kind:
            continue
        out.append(rec)
    return out[-limit:]


def summarize_by_route() -> dict[str, Any]:
    """按 route 聚合：每条路线各类评分的最新值 + 与上一条的差值（趋势）。"""
    records = read_records(limit=10000)
    by: dict[str, dict[str, list]] = {}
    for r in records:
        route = r.get("route", "unknown")
        kind = r.get("kind", "structural")
        by.setdefault(route, {}).setdefault(kind, []).append(r)

    summary: dict[str, Any] = {}
    for route, kinds in by.items():
        summary[route] = {}
        for kind, recs in kinds.items():
            recs_sorted = sorted(recs, key=lambda x: x.get("ts", 0))
            latest = recs_sorted[-1].get("overall")
            prev = recs_sorted[-2].get("overall") if len(recs_sorted) >= 2 else None
            delta = (round(latest - prev, 2) if (latest is not None and prev is not None) else None)
            summary[route][kind] = {
                "latest": latest,
                "previous": prev,
                "delta": delta,
                "count": len(recs_sorted),
            }
    return summary
