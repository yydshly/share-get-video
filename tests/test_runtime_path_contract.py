"""
Tests for the runtime path contract (path_contract.py) and related URL/path utilities.

Covers:
- path_to_runtime_url: default RUNTIME_DIR and custom RUNTIME_DIR
- runtime_url_to_path: all supported URL formats
- strip_runtime_url_prefix: default /runtime and custom prefix
- Style gallery to_runtime_url: uses PUBLIC_RUNTIME_URL_PREFIX
- No double /runtime/runtime/ paths
- Custom prefix (/assets) stripping
"""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestStripRuntimeUrlPrefix:
    """Tests for strip_runtime_url_prefix (backend helper)."""

    def test_strip_default_runtime_prefix(self):
        from app.video_lab.router import _strip_runtime_url_prefix
        assert _strip_runtime_url_prefix("/runtime/video_lab/x.mp4") == "video_lab/x.mp4"
        assert _strip_runtime_url_prefix("/runtime/video_lab/experiments/exp_a/final.mp4") == "video_lab/experiments/exp_a/final.mp4"

    def test_strip_custom_prefix(self, monkeypatch):
        import importlib
        import app.video_lab.router as router_module
        import app.video_lab.config as config_module

        monkeypatch.setenv("PUBLIC_RUNTIME_URL_PREFIX", "/assets")
        importlib.reload(config_module)
        importlib.reload(router_module)

        from app.video_lab.router import _strip_runtime_url_prefix

        assert _strip_runtime_url_prefix("/assets/video_lab/x.mp4") == "video_lab/x.mp4"

        # Restore
        monkeypatch.delenv("PUBLIC_RUNTIME_URL_PREFIX", raising=False)
        importlib.reload(config_module)
        importlib.reload(router_module)

    def test_strip_empty_url(self):
        from app.video_lab.router import _strip_runtime_url_prefix
        assert _strip_runtime_url_prefix("") == ""
        assert _strip_runtime_url_prefix(None) == ""

    def test_strip_fallback_without_prefix(self):
        from app.video_lab.router import _strip_runtime_url_prefix
        assert _strip_runtime_url_prefix("/other/video_lab/x.mp4") == "other/video_lab/x.mp4"


class TestRuntimeUrlToPath:
    """Tests for runtime_url_to_path.

    All paths are returned inside RUNTIME_DIR so custom VIDEO_LAB_RUNTIME_DIR
    (e.g. D:/custom-runtime) is respected. Use .as_posix() for OS-agnostic
    forward-slash comparison on Windows.
    """

    def test_strip_default_runtime(self):
        """URLs under /runtime/ map to RUNTIME_DIR/video_lab/..."""
        from app.video_lab.path_contract import runtime_url_to_path
        from app.video_lab.config import RUNTIME_DIR
        p = runtime_url_to_path("/runtime/video_lab/experiments/exp_a/final.mp4")
        assert p.as_posix().endswith("video_lab/experiments/exp_a/final.mp4")
        assert p.as_posix().startswith(str(RUNTIME_DIR).replace("\\", "/"))

    def test_strip_custom_prefix_assets(self):
        """URLs under /assets/ map to RUNTIME_DIR/video_lab/... (assets is a prefix, not a dir)."""
        from app.video_lab.path_contract import runtime_url_to_path
        from app.video_lab.config import RUNTIME_DIR
        p = runtime_url_to_path("/assets/video_lab/experiments/exp_a/final.mp4")
        assert p.as_posix().endswith("video_lab/experiments/exp_a/final.mp4")
        assert p.as_posix().startswith(str(RUNTIME_DIR).replace("\\", "/"))

    def test_bare_video_lab_path(self):
        """Bare video_lab/... gets RUNTIME_DIR prepended."""
        from app.video_lab.path_contract import runtime_url_to_path
        from app.video_lab.config import RUNTIME_DIR
        p = runtime_url_to_path("video_lab/experiments/exp_a/final.mp4")
        assert p.as_posix().endswith("video_lab/experiments/exp_a/final.mp4")
        assert p.as_posix().startswith(str(RUNTIME_DIR).replace("\\", "/"))

    def test_runtime_prefix_path(self):
        """runtime/... gets RUNTIME_DIR prepended (no double runtime/runtime)."""
        from app.video_lab.path_contract import runtime_url_to_path
        from app.video_lab.config import RUNTIME_DIR
        p = runtime_url_to_path("runtime/video_lab/experiments/exp_a/final.mp4")
        assert p.as_posix().endswith("video_lab/experiments/exp_a/final.mp4")
        assert not p.as_posix().startswith("runtime/runtime/")

    def test_full_url_with_scheme(self):
        """Full http:// URL with /runtime/ maps to RUNTIME_DIR/video_lab/..."""
        from app.video_lab.path_contract import runtime_url_to_path
        from app.video_lab.config import RUNTIME_DIR
        p = runtime_url_to_path("http://localhost:8000/runtime/video_lab/x.mp4")
        assert p.as_posix().endswith("video_lab/x.mp4")
        assert p.as_posix().startswith(str(RUNTIME_DIR).replace("\\", "/"))

    def test_full_url_with_assets_prefix(self):
        """Full http:// URL with /assets/ maps to RUNTIME_DIR/video_lab/... (prefix stripped)."""
        from app.video_lab.path_contract import runtime_url_to_path
        from app.video_lab.config import RUNTIME_DIR
        p = runtime_url_to_path("http://localhost:8000/assets/video_lab/x.mp4")
        assert p.as_posix().endswith("video_lab/x.mp4")
        assert p.as_posix().startswith(str(RUNTIME_DIR).replace("\\", "/"))

    def test_empty_string(self):
        from app.video_lab.path_contract import runtime_url_to_path
        p = runtime_url_to_path("")
        assert p == Path()

    def test_historical_runtime_url_under_custom_assets_prefix(self, monkeypatch):
        """Historical /runtime/... stored URLs are resolved even when prefix=/assets."""
        import importlib
        import app.video_lab.config as config_module
        import app.video_lab.path_contract as path_contract_module

        monkeypatch.setenv("PUBLIC_RUNTIME_URL_PREFIX", "/assets")
        importlib.reload(config_module)
        importlib.reload(path_contract_module)

        from app.video_lab.config import RUNTIME_DIR
        from app.video_lab.path_contract import runtime_url_to_path

        p = runtime_url_to_path("/runtime/video_lab/experiments/exp_a/final.mp4")

        assert p.as_posix().endswith("video_lab/experiments/exp_a/final.mp4")
        assert p.as_posix().startswith(str(RUNTIME_DIR).replace("\\", "/"))
        assert "/runtime/runtime/" not in p.as_posix().replace("\\", "/")

        monkeypatch.delenv("PUBLIC_RUNTIME_URL_PREFIX", raising=False)
        importlib.reload(config_module)
        importlib.reload(path_contract_module)


class TestPathToRuntimeUrl:
    """Tests for path_to_runtime_url (via file_store.path_to_url)."""

    def test_default_runtime_no_double_prefix(self, monkeypatch):
        import importlib
        import app.video_lab.config as config_module
        import app.video_lab.renderers.file_store as file_store_module

        monkeypatch.delenv("VIDEO_LAB_RUNTIME_DIR", raising=False)
        monkeypatch.delenv("PUBLIC_RUNTIME_URL_PREFIX", raising=False)

        importlib.reload(config_module)
        importlib.reload(file_store_module)

        from app.video_lab.renderers.file_store import path_to_url

        url = path_to_url("runtime/video_lab/experiments/exp_a/final.mp4")
        assert url == "/runtime/video_lab/experiments/exp_a/final.mp4"
        assert not url.startswith("/runtime/runtime/")

    def test_custom_runtime_dir_maps_to_runtime_prefix(self, monkeypatch, tmp_path):
        """Custom RUNTIME_DIR should map to /runtime/... not expose the custom path."""
        import importlib
        import app.video_lab.config as config_module
        import app.video_lab.renderers.file_store as file_store_module

        custom_runtime = tmp_path / "custom-runtime"
        custom_runtime.mkdir()

        monkeypatch.setenv("VIDEO_LAB_RUNTIME_DIR", str(custom_runtime))
        monkeypatch.setenv("PUBLIC_RUNTIME_URL_PREFIX", "/runtime")

        importlib.reload(config_module)
        importlib.reload(file_store_module)

        from app.video_lab.renderers.file_store import path_to_url

        test_file = custom_runtime / "video_lab" / "experiments" / "exp_b" / "final.mp4"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("video")

        url = path_to_url(str(test_file))

        assert url.startswith("/runtime/")
        assert "/D:/" not in url
        assert "/tmp/" not in url
        assert "custom-runtime" not in url

        # Restore defaults
        monkeypatch.delenv("VIDEO_LAB_RUNTIME_DIR", raising=False)
        monkeypatch.delenv("PUBLIC_RUNTIME_URL_PREFIX", raising=False)
        importlib.reload(config_module)
        importlib.reload(file_store_module)


class TestStyleGalleryToRuntimeUrl:
    """Tests for style_gallery store.to_runtime_url with custom prefix."""

    def test_to_runtime_url_default(self, monkeypatch):
        import importlib
        import app.video_lab.config as config_module
        import app.video_lab.style_gallery.store as store_module

        monkeypatch.delenv("PUBLIC_RUNTIME_URL_PREFIX", raising=False)
        importlib.reload(config_module)
        importlib.reload(store_module)

        from app.video_lab.style_gallery.store import to_runtime_url

        assert to_runtime_url("/runtime/video_lab/x.mp4") == "/runtime/video_lab/x.mp4"
        assert to_runtime_url("video_lab/x.mp4") == "/runtime/video_lab/x.mp4"
        assert to_runtime_url("style_gallery/records/rec.jsonl") == "/runtime/style_gallery/records/rec.jsonl"

    def test_to_runtime_url_custom_prefix(self, monkeypatch):
        import importlib
        import app.video_lab.config as config_module
        import app.video_lab.style_gallery.store as store_module

        monkeypatch.setenv("PUBLIC_RUNTIME_URL_PREFIX", "/assets")
        importlib.reload(config_module)
        importlib.reload(store_module)

        from app.video_lab.style_gallery.store import to_runtime_url

        # /runtime/ should be replaced with /assets/
        assert to_runtime_url("/runtime/video_lab/x.mp4") == "/assets/video_lab/x.mp4"
        # video_lab/... should get /assets/ prefix
        assert to_runtime_url("video_lab/x.mp4") == "/assets/video_lab/x.mp4"
        # style_gallery/... should get /assets/ prefix
        assert to_runtime_url("style_gallery/records/rec.jsonl") == "/assets/style_gallery/records/rec.jsonl"

        # Restore
        monkeypatch.delenv("PUBLIC_RUNTIME_URL_PREFIX", raising=False)
        importlib.reload(config_module)
        importlib.reload(store_module)
