"""
style_gallery/compare_bundle.py - Compare Bundle for Style Sample comparisons
V1.0.7: Compare Bundle — save and replay style sample comparison decisions
"""

import json
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.video_lab.style_gallery import store as sg_store
from app.video_lab.config import RUNTIME_DIR


# ─── 路径常量 ────────────────────────────────────────────────────────────────

_RUNTIME = RUNTIME_DIR / "style_gallery"
_RECORDS_DIR = _RUNTIME / "records"
_JSONL_PATH = _RECORDS_DIR / "compare_bundles.jsonl"


def _ensure_dirs() -> None:
    """确保目录存在。"""
    _RECORDS_DIR.mkdir(parents=True, exist_ok=True)


# ─── 数据模型 ────────────────────────────────────────────────────────────────

class CompareBundleItem(BaseModel):
    sample_id: str
    route_id: str = ""
    route_name: str = ""
    style_name: str = ""
    status: str = ""
    score: float | None = None
    grade: str = ""
    video_url: str = ""
    poster_url: str = ""
    manifest_url: str = ""
    rerun_payload_available: bool = False
    notes: str = ""


class CompareBundleDecision(BaseModel):
    winner_sample_id: str = ""
    winner_reason: str = ""
    rejected_sample_ids: list[str] = Field(default_factory=list)
    rejected_reasons: dict[str, str] = Field(default_factory=dict)
    productization_notes: str = ""


class CompareBundle(BaseModel):
    id: str
    title: str = ""
    goal: str = ""
    sample_ids: list[str] = Field(default_factory=list)
    items: list[CompareBundleItem] = Field(default_factory=list)
    decision: CompareBundleDecision = Field(default_factory=CompareBundleDecision)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    schema_version: str = "1.0.7"

    def to_dict(self) -> dict[str, Any]:
        d = self.model_dump(mode="json")
        d["created_at"] = self.created_at.isoformat()
        d["updated_at"] = self.updated_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "CompareBundle":
        if isinstance(d.get("created_at"), str):
            d["created_at"] = datetime.fromisoformat(d["created_at"])
        if isinstance(d.get("updated_at"), str):
            d["updated_at"] = datetime.fromisoformat(d["updated_at"])
        if "decision" not in d:
            d["decision"] = {}
        if "items" not in d:
            d["items"] = []
        if "tags" not in d:
            d["tags"] = []
        if "schema_version" not in d:
            d["schema_version"] = "1.0.7"
        return cls(**d)


# ─── ID 生成 ────────────────────────────────────────────────────────────────

def new_bundle_id() -> str:
    return f"bundle_{uuid.uuid4().hex[:8]}"


# ─── JSONL 存储 ─────────────────────────────────────────────────────────────

def _read_all() -> list[dict[str, Any]]:
    """读取所有对比包记录（按 updated_at 倒序）。"""
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


def list_compare_bundles(limit: int = 50) -> list[CompareBundle]:
    """列出所有对比包，按 updated_at 倒序。"""
    records = _read_all()
    bundles = [CompareBundle.from_dict(r) for r in records]
    bundles.sort(key=lambda b: b.updated_at, reverse=True)
    return bundles[:limit]


def get_compare_bundle(bundle_id: str) -> CompareBundle | None:
    """按 ID 查询对比包。"""
    records = _read_all()
    for r in records:
        if r.get("id") == bundle_id:
            return CompareBundle.from_dict(r)
    return None


def save_compare_bundle(bundle: CompareBundle) -> CompareBundle:
    """新增或更新一个对比包（按 ID 全量覆盖）。"""
    _ensure_dirs()
    records = _read_all()
    bundle.updated_at = datetime.utcnow()
    idx = next((i for i, r in enumerate(records) if r.get("id") == bundle.id), -1)
    d = bundle.to_dict()
    if idx >= 0:
        records[idx] = d
    else:
        records.append(d)
    _write_all(records)
    return bundle


def delete_compare_bundle(bundle_id: str) -> bool:
    """删除一个对比包。"""
    records = _read_all()
    before = len(records)
    records = [r for r in records if r.get("id") != bundle_id]
    if len(records) == before:
        return False
    _write_all(records)
    return True


# ─── 构建对比包 ─────────────────────────────────────────────────────────────

def build_compare_bundle(
    sample_ids: list[str],
    title: str = "",
    goal: str = "",
    tags: list[str] | None = None,
) -> CompareBundle:
    """从一组 sample_id 创建 CompareBundle。

    逻辑：
    1. 根据 sample_ids 从 sg_store.get_sample() 获取样片。
    2. 不存在的 sample_id 跳过（警告）。
    3. items 从 StyleSample 中提取字段。
    4. winner 默认选 visual_judgement.score 最高者。
    5. 如果所有样片都没有 score，winner 为空。
    6. winner_reason 自动生成。
    7. rejected_sample_ids 默认是非 winner 的样片。
    """
    bundle_id = new_bundle_id()
    now = datetime.utcnow()
    items: list[CompareBundleItem] = []
    found_ids: list[str] = []

    for sid in sample_ids:
        sample = sg_store.get_sample(sid)
        if not sample:
            continue
        found_ids.append(sid)
        urls = sg_store.resolve_sample_urls(sample)
        score = sample.visual_judgement.score if sample.visual_judgement else None
        grade = sample.visual_judgement.grade if sample.visual_judgement else ""
        rerun_available = bool(
            sample.params.get("fullContent") or sample.params.get("content") or sample.content_preview
        )
        item = CompareBundleItem(
            sample_id=sample.id,
            route_id=sample.route_id,
            route_name=sample.route_name,
            style_name=sample.style_name,
            status=sample.status.value if hasattr(sample.status, "value") else str(sample.status),
            score=score,
            grade=grade,
            video_url=urls.get("video_url", ""),
            poster_url=urls.get("poster_url", ""),
            manifest_url=urls.get("manifest_url", ""),
            rerun_payload_available=rerun_available,
        )
        items.append(item)

    # 推导 winner：score 最高者
    scored_items = [it for it in items if it.score is not None]
    if scored_items:
        winner_item = max(scored_items, key=lambda it: it.score)
        winner_id = winner_item.sample_id
        winner_reason = f"视觉评分最高：{winner_item.score}分（{winner_item.grade}）"
    else:
        winner_id = ""
        winner_reason = "暂无视觉评分，需人工判断"

    # rejected 是非 winner 的样片
    rejected_ids = [sid for sid in found_ids if sid != winner_id]

    if not title:
        title = f"样片对比包 {now.strftime('%Y-%m-%d %H:%M')}"

    bundle = CompareBundle(
        id=bundle_id,
        title=title,
        goal=goal,
        sample_ids=found_ids,
        items=items,
        decision=CompareBundleDecision(
            winner_sample_id=winner_id,
            winner_reason=winner_reason,
            rejected_sample_ids=rejected_ids,
            rejected_reasons={sid: "对比中未胜出" for sid in rejected_ids},
        ),
        tags=tags or [],
        created_at=now,
        updated_at=now,
        schema_version="1.0.7",
    )
    return bundle
