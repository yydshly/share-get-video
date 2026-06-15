"""
style_gallery/score_history.py - 样片评分历史留痕（V0.4.4）

每次对样片做视觉评分都追加一条记录，使"历史可分析"成立：
- 同一样片可多次评分，保留每次结果（visual_judgement 在样片上是覆盖的，这里是 append-only）
- 可按路线聚合，看每条路线评分的最新值 + 趋势（涨跌）

分制与 Style Gallery 一致（0-100），独立于 quality/quality_log.py（那里是 1-5），不混用。
JSONL 存储，无数据库；_JSONL_PATH 可在测试中 monkeypatch 到临时目录。
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

_RUNTIME = Path(__file__).parent.parent.parent.parent.parent / "runtime" / "style_gallery"
_RECORDS_DIR = _RUNTIME / "records"
_JSONL_PATH = _RECORDS_DIR / "score_history.jsonl"


def _ensure_dirs() -> None:
    _RECORDS_DIR.mkdir(parents=True, exist_ok=True)


def append_score(record: dict[str, Any]) -> dict[str, Any]:
    """追加一条评分记录（自动加时间戳）。"""
    rec = {"ts": time.time(), "isoTime": datetime.utcnow().isoformat(), **record}
    _ensure_dirs()
    with open(_JSONL_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def read_scores(
    route_id: str | None = None,
    sample_id: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """读取评分历史（可按 route / sample 过滤），返回最近 limit 条。"""
    if not _JSONL_PATH.exists():
        return []
    out: list[dict[str, Any]] = []
    with open(_JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if route_id and rec.get("route_id") != route_id:
                continue
            if sample_id and rec.get("sampleId") != sample_id:
                continue
            out.append(rec)
    return out[-limit:]


def summarize_by_route() -> dict[str, Any]:
    """按路线聚合：最新分 / 上一次 / 涨跌 delta / 次数 / 平均分。"""
    records = read_scores(limit=100000)
    by: dict[str, list[dict[str, Any]]] = {}
    for r in records:
        by.setdefault(r.get("route_id", "unknown"), []).append(r)

    summary: dict[str, Any] = {}
    for route, recs in by.items():
        recs_sorted = sorted(recs, key=lambda x: x.get("ts", 0))
        scores = [float(r["score"]) for r in recs_sorted if r.get("score") is not None]
        latest = scores[-1] if scores else None
        prev = scores[-2] if len(scores) >= 2 else None
        delta = round(latest - prev, 1) if (latest is not None and prev is not None) else None
        avg = round(sum(scores) / len(scores), 1) if scores else None
        summary[route] = {
            "routeName": recs_sorted[-1].get("route_name", route),
            "latest": latest,
            "previous": prev,
            "delta": delta,
            "average": avg,
            "count": len(recs_sorted),
        }
    return summary
