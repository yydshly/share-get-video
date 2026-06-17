"""
tests/test_style_gallery_store_datetime.py
Stage 2B-FIX: datetime naive/aware compatibility for Style Gallery store.

Covers:
1. list_samples can sort mixed naive and aware created_at datetimes
2. Old record with created_at = "2026-01-01T10:00:00" (naive) does not crash
3. New record with created_at = "2026-01-01T10:00:00+00:00" (aware) does not crash
4. list_samples returns results in reverse chronological order
5. route-fit related calls do not crash due to list_samples sorting
"""

import sys
import os
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pathlib import Path

from app.video_lab.style_gallery import store as sg_store


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_store(monkeypatch, tmp_path):
    """Redirect store paths to a temp directory."""
    runtime = tmp_path / "runtime" / "style_gallery"
    records_dir = runtime / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = records_dir / "style_samples.jsonl"

    monkeypatch.setattr(sg_store, "_RUNTIME", runtime)
    monkeypatch.setattr(sg_store, "_RECORDS_DIR", records_dir)
    monkeypatch.setattr(sg_store, "_JSONL_PATH", jsonl_path)
    return records_dir


def _write_jsonl(records_dir: Path, records: list[dict]) -> None:
    """Write records to the JSONL file."""
    jsonl_path = records_dir / "style_samples.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ─── Tests ────────────────────────────────────────────────────────────────────

def test_list_samples_sorts_naive_datetime_only(temp_store):
    """list_samples does not crash when all records have naive (no tz) created_at."""
    records = [
        {
            "id": "sample_naive_old",
            "route_id": "local_frame_compose",
            "route_name": "Pillow",
            "style_name": "Old Style",
            "status": "candidate",
            "params": {},
            "output": {"type": "mp4", "path": "a.mp4"},
            "evaluation": {},
            "tags": [],
            "created_at": "2026-01-01T10:00:00",  # naive
        },
        {
            "id": "sample_naive_new",
            "route_id": "local_frame_compose",
            "route_name": "Pillow",
            "style_name": "New Style",
            "status": "candidate",
            "params": {},
            "output": {"type": "mp4", "path": "b.mp4"},
            "evaluation": {},
            "tags": [],
            "created_at": "2026-06-01T10:00:00",  # naive, newer
        },
    ]
    _write_jsonl(temp_store, records)

    samples = sg_store.list_samples(limit=50)
    assert len(samples) == 2
    # Newer should come first (reverse chronological)
    assert samples[0].id == "sample_naive_new"
    assert samples[1].id == "sample_naive_old"


def test_list_samples_sorts_aware_datetime_only(temp_store):
    """list_samples does not crash when all records have UTC-aware created_at."""
    records = [
        {
            "id": "sample_aware_old",
            "route_id": "template_programmatic_render",
            "route_name": "Remotion",
            "style_name": "Old Motion",
            "status": "candidate",
            "params": {},
            "output": {"type": "mp4", "path": "c.mp4"},
            "evaluation": {},
            "tags": [],
            "created_at": "2026-01-01T10:00:00+00:00",  # UTC-aware
        },
        {
            "id": "sample_aware_new",
            "route_id": "template_programmatic_render",
            "route_name": "Remotion",
            "style_name": "New Motion",
            "status": "candidate",
            "params": {},
            "output": {"type": "mp4", "path": "d.mp4"},
            "evaluation": {},
            "tags": [],
            "created_at": "2026-06-01T10:00:00+00:00",  # UTC-aware, newer
        },
    ]
    _write_jsonl(temp_store, records)

    samples = sg_store.list_samples(limit=50)
    assert len(samples) == 2
    assert samples[0].id == "sample_aware_new"
    assert samples[1].id == "sample_aware_old"


def test_list_samples_sorts_mixed_naive_and_aware_datetimes(temp_store):
    """list_samples does not crash when records have mixed naive and aware datetimes."""
    records = [
        {
            "id": "sample_naive_old",
            "route_id": "local_frame_compose",
            "route_name": "Pillow",
            "style_name": "Naive Old",
            "status": "candidate",
            "params": {},
            "output": {"type": "mp4", "path": "e.mp4"},
            "evaluation": {},
            "tags": [],
            "created_at": "2026-01-01T10:00:00",  # naive
        },
        {
            "id": "sample_aware_new",
            "route_id": "local_frame_compose",
            "route_name": "Pillow",
            "style_name": "Aware New",
            "status": "candidate",
            "params": {},
            "output": {"type": "mp4", "path": "f.mp4"},
            "evaluation": {},
            "tags": [],
            "created_at": "2026-06-01T10:00:00+00:00",  # UTC-aware, newer
        },
        {
            "id": "sample_naive_mid",
            "route_id": "local_frame_compose",
            "route_name": "Pillow",
            "style_name": "Naive Mid",
            "status": "candidate",
            "params": {},
            "output": {"type": "mp4", "path": "g.mp4"},
            "evaluation": {},
            "tags": [],
            "created_at": "2026-04-01T10:00:00",  # naive, mid
        },
    ]
    _write_jsonl(temp_store, records)

    # Must not raise TypeError: can't compare offset-naive and offset-aware datetimes
    samples = sg_store.list_samples(limit=50)
    assert len(samples) == 3
    # Should be in reverse chronological order
    ids = [s.id for s in samples]
    assert ids[0] == "sample_aware_new"        # newest (June, aware)
    assert ids[1] == "sample_naive_mid"        # mid (April, naive)
    assert ids[2] == "sample_naive_old"        # oldest (Jan, naive)


def test_list_samples_respects_limit(temp_store):
    """list_samples respects the limit parameter."""
    records = [
        {
            "id": f"sample_{i:03d}",
            "route_id": "local_frame_compose",
            "route_name": "Pillow",
            "style_name": f"Style {i}",
            "status": "candidate",
            "params": {},
            "output": {"type": "mp4", "path": f"{i}.mp4"},
            "evaluation": {},
            "tags": [],
            "created_at": f"2026-01-{i+1:02d}T10:00:00",  # naive
        }
        for i in range(10)
    ]
    _write_jsonl(temp_store, records)

    samples = sg_store.list_samples(limit=3)
    assert len(samples) == 3


def test_from_dict_normalizes_naive_created_at_to_utc():
    """StyleSample.from_dict converts naive datetime to UTC-aware."""
    from app.video_lab.style_gallery.models import StyleSample

    d = {
        "id": "sample_test",
        "route_id": "local_frame_compose",
        "route_name": "Pillow",
        "style_name": "Test",
        "status": "candidate",
        "params": {},
        "output": {"type": "mp4", "path": "t.mp4"},
        "evaluation": {},
        "tags": [],
        "created_at": "2026-06-01T10:00:00",  # naive
    }
    sample = StyleSample.from_dict(d)
    assert sample.created_at.tzinfo is not None  # now aware
    assert sample.created_at.tzinfo == timezone.utc


def test_from_dict_keeps_aware_created_at_intact():
    """StyleSample.from_dict does not modify an already-aware datetime."""
    from app.video_lab.style_gallery.models import StyleSample

    d = {
        "id": "sample_test2",
        "route_id": "local_frame_compose",
        "route_name": "Pillow",
        "style_name": "Test2",
        "status": "candidate",
        "params": {},
        "output": {"type": "mp4", "path": "t2.mp4"},
        "evaluation": {},
        "tags": [],
        "created_at": "2026-06-01T10:00:00+00:00",  # already UTC-aware
    }
    sample = StyleSample.from_dict(d)
    assert sample.created_at.tzinfo is not None
    assert sample.created_at == datetime.fromisoformat("2026-06-01T10:00:00+00:00")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
