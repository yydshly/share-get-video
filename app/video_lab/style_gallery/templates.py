"""
style_gallery/templates.py - Style Template data model and JSONL storage
V0.4.2: Style Sample promotion to template — lightweight JSONL-backed template records
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class StyleTemplate(BaseModel):
    """一条风格模板记录。"""

    id: str = Field(..., description="模板唯一ID，格式 template_xxxx")
    name: str = Field(..., description="模板展示名称")
    route_id: str = Field(..., description="视觉路线 routeId")
    route_name: str = Field(..., description="路线展示名")
    style_name: str = Field(..., description="原始风格名称")
    description: str = Field(default="", description="模板描述")
    params: dict[str, Any] = Field(default_factory=dict, description="生成参数")
    source_sample_id: str = Field(..., description="来源样片ID")
    source_sample_score: float | None = Field(default=None, description="来源样片评分")
    visual_judgement: dict[str, Any] | None = Field(default=None, description="视觉评分结果")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

    def to_dict(self) -> dict[str, Any]:
        d = self.model_dump(mode="json")
        d["created_at"] = self.created_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "StyleTemplate":
        if isinstance(d.get("created_at"), str):
            d["created_at"] = datetime.fromisoformat(d["created_at"])
        return cls(**d)


# ─── JSONL Storage ────────────────────────────────────────────────────────────

_RUNTIME = Path(__file__).parent.parent.parent.parent.parent / "runtime" / "style_gallery"
_RECORDS_DIR = _RUNTIME / "records"
_JSONL_PATH = _RECORDS_DIR / "style_templates.jsonl"


def _ensure_dirs() -> None:
    _RECORDS_DIR.mkdir(parents=True, exist_ok=True)


def _read_all() -> list[dict[str, Any]]:
    """读取所有模板记录。"""
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


def list_templates(route_id: str | None = None) -> list[StyleTemplate]:
    """列出模板，支持按路线过滤。"""
    records = _read_all()
    results = []
    for r in records:
        if route_id and r.get("route_id") != route_id:
            continue
        results.append(StyleTemplate.from_dict(r))
    results.sort(key=lambda t: t.created_at, reverse=True)
    return results


def get_template(template_id: str) -> StyleTemplate | None:
    """按 ID 查询模板。"""
    records = _read_all()
    for r in records:
        if r.get("id") == template_id:
            return StyleTemplate.from_dict(r)
    return None


def find_by_source_sample(sample_id: str) -> StyleTemplate | None:
    """按来源样片 ID 查找已存在的模板（用于升级去重）。"""
    for r in _read_all():
        if r.get("source_sample_id") == sample_id:
            return StyleTemplate.from_dict(r)
    return None


def save_template(template: StyleTemplate) -> StyleTemplate:
    """新增或更新一条模板记录（按 ID 全量覆盖）。"""
    _ensure_dirs()
    records = _read_all()
    idx = next((i for i, r in enumerate(records) if r.get("id") == template.id), -1)
    d = template.to_dict()
    if idx >= 0:
        records[idx] = d
    else:
        records.append(d)
    _write_all(records)
    return template


def delete_template(template_id: str) -> bool:
    """删除一条模板记录。"""
    records = _read_all()
    before = len(records)
    records = [r for r in records if r.get("id") != template_id]
    if len(records) == before:
        return False
    _write_all(records)
    return True
