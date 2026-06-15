#!/usr/bin/env python3
"""
Preflight check script for new machine setup.

Run this before starting the app to quickly diagnose missing dependencies
and configuration issues.

Usage:
    python scripts/preflight_new_machine.py

Exit codes:
    0  - all critical checks passed
    1  - one or more critical checks failed
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "app"
FRONTEND_ROOT = PROJECT_ROOT / "frontend"

# Load .env before reading any env vars (override=False so system env takes precedence)
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env", override=False)
except Exception:
    pass


def resolve_project_path(p: str | Path) -> Path:
    """Resolve a potentially-relative path relative to PROJECT_ROOT."""
    path = Path(p)
    return path if path.is_absolute() else PROJECT_ROOT / path


# Runtime dir from config (env var or default)
RUNTIME_DIR = resolve_project_path(os.getenv("VIDEO_LAB_RUNTIME_DIR", "runtime"))

# Remotion workspace from config
try:
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from app.video_lab.config import REMOTION_DIR
    REMOTION_ROOT = REMOTION_DIR
except Exception:
    REMOTION_ROOT = PROJECT_ROOT / "remotion"


def check(name: str, condition: bool, detail: str = "", warn: bool = False) -> bool:
    tag = "[WARN]" if warn else ("[OK]" if condition else "[FAIL]")
    print(f"  {tag} {name}")
    if detail:
        print(f"       {detail}")
    return condition


def run_cmd(cmd: list[str], **kwargs) -> tuple[int, str, str]:
    """Run a command, return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            **kwargs,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return -1, "", f"{cmd[0]} not found"
    except subprocess.TimeoutExpired:
        return -2, "", "command timed out"
    except Exception as e:
        return -3, "", str(e)


def main() -> int:
    print("\n=== Video Lab Preflight Check ===")
    print(f"Project root: {PROJECT_ROOT}\n")

    all_ok = True

    # ── Python ──────────────────────────────────────────────────────────────────
    print("[ Python ]")
    ver = sys.version_info
    py_ok = check("Python version", ver >= (3, 10), f"{ver.major}.{ver.minor}.{ver.micro}")
    all_ok &= py_ok

    # ── Backend imports ──────────────────────────────────────────────────────────
    print("\n[ Backend imports ]")
    backend_modules = ["fastapi", "uvicorn", "dotenv"]
    for mod in backend_modules:
        try:
            __import__(mod)
            check(mod, True)
        except ImportError:
            check(mod, False, f"pip install {mod}")
            all_ok = False

    # ── .env ────────────────────────────────────────────────────────────────────
    print("\n[ .env configuration ]")
    env_file = PROJECT_ROOT / ".env"
    env_example = PROJECT_ROOT / ".env.example"
    if env_file.exists():
        check(".env exists", True)
        # Check key values
        from dotenv import dotenv_values
        vals = dotenv_values(env_file)
        check("MINIMAX_API_KEY", bool(vals.get("MINIMAX_API_KEY", "").strip()),
              warn=not vals.get("MINIMAX_API_KEY", "").strip())
        check("MINIMAX_GROUP_ID", bool(vals.get("MINIMAX_GROUP_ID", "").strip()),
              warn=not vals.get("MINIMAX_GROUP_ID", "").strip())
    else:
        if env_example.exists():
            check(".env exists", False,
                 f"copy {env_example.relative_to(PROJECT_ROOT)} → .env and fill in your keys")
        else:
            check(".env exists", False, ".env.example not found — cannot copy")
        all_ok = False

    # ── runtime directory ────────────────────────────────────────────────────────
    print("\n[ Runtime directory ]")
    try:
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        test_file = RUNTIME_DIR / ".preflight_test"
        test_file.write_text("ok")
        test_file.unlink()
        check(f"runtime dir writable ({RUNTIME_DIR})", True, str(RUNTIME_DIR))
    except Exception as e:
        check(f"runtime dir writable ({RUNTIME_DIR})", False, str(e))
        all_ok = False

    # ── ffmpeg / ffprobe ────────────────────────────────────────────────────────
    print("\n[ External binaries ]")
    for binary, env_var in [("ffmpeg", "FFMPEG_BINARY"), ("ffprobe", "FFPROBE_BINARY")]:
        explicit = os.getenv(env_var, "").strip()
        if explicit:
            # Explicit path: check file exists (resolve relative to project root)
            resolved = resolve_project_path(explicit)
            found = resolved.exists()
            check(f"{binary} ({env_var})", found, str(resolved))
            all_ok &= found
        else:
            found = shutil.which(binary)
            check(binary, bool(found), "found in PATH" if found else "not in PATH — install ffmpeg")
            if not found:
                all_ok = False

    # ── Node / npm ──────────────────────────────────────────────────────────────
    print("\n[ Node.js ]")
    rc, stdout, _ = run_cmd(["node", "--version"])
    node_ok = rc == 0
    check("node", node_ok, stdout if node_ok else "not found — install Node.js")
    all_ok &= node_ok

    rc, stdout, _ = run_cmd(["npm", "--version"])
    npm_ok = rc == 0
    check("npm", npm_ok, stdout if npm_ok else "not found — install npm")
    all_ok &= npm_ok

    # ── frontend .env ───────────────────────────────────────────────────────────
    print("\n[ Frontend ]")
    fe_env = FRONTEND_ROOT / ".env"
    fe_env_example = FRONTEND_ROOT / ".env.example"
    if fe_env.exists():
        check("frontend/.env exists", True)
    else:
        if fe_env_example.exists():
            check("frontend/.env exists", False,
                 f"copy {fe_env_example.relative_to(PROJECT_ROOT)} → frontend/.env")
        all_ok = False

    if (FRONTEND_ROOT / "package.json").exists():
        check("frontend/package.json", True)
    else:
        check("frontend/package.json", False)
        all_ok = False

    # ── remotion ────────────────────────────────────────────────────────────────
    print("\n[ Remotion ]")
    remotion_pkg = REMOTION_ROOT / "package.json"
    if remotion_pkg.exists():
        check("remotion/package.json", True)
        node_modules = REMOTION_ROOT / "node_modules"
        if node_modules.exists():
            check("remotion/node_modules", True)
        else:
            check("remotion/node_modules", False,
                  f"cd {REMOTION_ROOT.relative_to(PROJECT_ROOT)} && npm install")
            all_ok = False

        rc, stdout, _ = run_cmd(["npx", "remotion", "--version"], cwd=REMOTION_ROOT)
        # npx remotion --version exits 1 but prints version info — treat as OK if output contains @
        if rc == 0 or "@remotion/" in stdout:
            check("npx remotion --version", True, stdout)
        else:
            check("npx remotion --version", False,
                  f"cd remotion && npm install  ({stdout or 'error'})")
            all_ok = False
    else:
        check("remotion/package.json", False,
              "remotion not set up — Pillow route still usable")
        all_ok = False

    # ── Backend smoke test ──────────────────────────────────────────────────────
    print("\n[ Backend smoke test ]")
    smoke_script = PROJECT_ROOT / "scripts" / "smoke_test.py"
    if smoke_script.exists():
        rc, stdout, stderr = run_cmd(
            [sys.executable, str(smoke_script)],
            cwd=PROJECT_ROOT,
        )
        if rc == 0:
            check("smoke_test.py", True, "passed")
        else:
            check("smoke_test.py", False, (stdout + " " + stderr).strip()[:120])
    else:
        check("smoke_test.py", False, "not found — skip backend smoke test")

    # ── Summary ────────────────────────────────────────────────────────────────
    print("\n=== Capability Tiers ===")
    minimax_ok = bool(os.getenv("MINIMAX_API_KEY") and os.getenv("MINIMAX_GROUP_ID"))
    ffmpeg_ok = shutil.which("ffmpeg") is not None or os.getenv("FFMPEG_BINARY")
    remotion_ok = (REMOTION_ROOT / "node_modules").exists()

    print(f"  [{('OK' if py_ok else '!!')}] UI only (backend boot)")
    print(f"  [{('OK' if ffmpeg_ok else '!!')}] Pillow route")
    print(f"  [{('OK' if remotion_ok else '!!')}] Remotion route")
    print(f"  [{('OK' if minimax_ok and ffmpeg_ok else '!!')}] Full TTS + video compose")

    print()
    if all_ok:
        print("Result: ALL CHECKS PASSED")
        return 0
    else:
        print("Result: SOME CHECKS FAILED — fix the [FAIL] items above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
