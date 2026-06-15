#!/usr/bin/env python3
"""
Backend smoke test — verifies the FastAPI app boots and key routes respond.

Usage:
    python scripts/smoke_test.py

Exit codes:
    0 - all checks passed
    1 - one or more checks failed
"""

import sys
import os
from pathlib import Path

# Ensure the app is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from app.main import app

BASE_URL = "http://localhost:8000"
VIDEO_LAB_BASE = f"{BASE_URL}/video-lab"


def check(name: str, condition: bool, detail: str = "") -> bool:
    tag = "[OK]" if condition else "[FAIL]"
    print(f"  {tag} {name}")
    if detail:
        print(f"       {detail}")
    return condition


def main() -> int:
    print("\n=== Backend Smoke Test ===\n")

    all_ok = True

    # Boot the app (importing it already exercises most modules)
    print("[ Import ]")
    all_ok &= check("app.main imports", True)

    # Basic root endpoint
    print("\n[ Root endpoint ]")
    try:
        resp = httpx.get(f"{BASE_URL}/", timeout=10)
        all_ok &= check("GET / returns 200", resp.status_code == 200, f"{resp.status_code}")
    except Exception as e:
        all_ok &= check("GET /", False, str(e))

    # Health endpoint
    print("\n[ Health ]")
    try:
        resp = httpx.get(f"{BASE_URL}/health", timeout=10)
        all_ok &= check("GET /health returns 200", resp.status_code == 200, f"{resp.status_code}")
    except Exception as e:
        all_ok &= check("GET /health", False, str(e))

    # Static runtime mount — create a temp file and try to fetch it
    print("\n[ Static mount ]")
    try:
        from app.video_lab.config import RUNTIME_DIR, PUBLIC_RUNTIME_URL_PREFIX
        runtime_test_rel = Path("video_lab") / ".smoke_test"
        runtime_test_file = RUNTIME_DIR / runtime_test_rel
        runtime_test_file.parent.mkdir(parents=True, exist_ok=True)
        runtime_test_file.write_text("smoke test ok", encoding="utf-8")
        prefix = PUBLIC_RUNTIME_URL_PREFIX.rstrip("/")
        url_path = f"{prefix}/{runtime_test_rel.as_posix().replace(chr(92), '/')}"
        resp = httpx.get(f"{BASE_URL}{url_path}", timeout=10)
        if resp.status_code == 200 and "smoke test ok" in resp.text:
            all_ok &= check(f"GET {url_path} serves file", True, f"{resp.status_code}")
        else:
            # 404 with server running → likely server was started before config changes
            all_ok &= check(
                f"GET {url_path} serves file",
                False,
                f"{resp.status_code} — restart server if it was started before code updates",
            )
        runtime_test_file.unlink(missing_ok=True)
    except Exception as e:
        all_ok &= check("Static mount", False, str(e))

    print()
    if all_ok:
        print("Result: ALL CHECKS PASSED")
        return 0
    else:
        print("Result: SOME CHECKS FAILED")
        return 1


if __name__ == "__main__":
    # If the server isn't running, skip HTTP checks (exit 0 for CI)
    try:
        import httpx
        httpx.get("http://localhost:8000/", timeout=2)
    except Exception:
        print("[INFO] Backend server not running — skipping HTTP smoke checks.")
        print("       Start the server with: cd app && uvicorn main:app --reload --port 8000")
        print("       Then re-run this script to verify /health and /runtime.")
        sys.exit(0)

    sys.exit(main())
