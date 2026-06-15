# New Machine Setup Guide

This guide walks you through setting up the Video Lab project on a new machine from scratch.

---

## Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- ffmpeg and ffprobe (for video processing)
- Git

---

## 1. Clone the repository

```bash
git clone https://github.com/yydshly/share-get-video.git
cd share-get-video
```

## 2. Switch to your working branch

```bash
git checkout feature/v0.3.6-b1-shotplan-standardization
```

## 3. Create a Python virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate          # Windows
```

## 4. Install backend dependencies

```bash
pip install -r requirements.txt
```

If you don't have a `requirements.txt`, install the core packages:

```bash
pip install fastapi uvicorn python-dotenv
pip install Pillow            # Pillow-based image rendering
pip install openai            # for LLM calls if used
```

## 5. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
# MiniMax TTS API — required for full TTS + video compose
MINIMAX_API_KEY=your_key_here
MINIMAX_GROUP_ID=your_group_id_here
```

Optional overrides (defaults work for most setups):

```env
# Custom runtime directory (default: runtime)
# VIDEO_LAB_RUNTIME_DIR=runtime

# Custom experiments output dir (default: runtime/video_lab/experiments)
# VIDEO_LAB_EXPERIMENTS_DIR=runtime/video_lab/experiments

# Custom URL prefix for static assets (default: /runtime)
# PUBLIC_RUNTIME_URL_PREFIX=/runtime

# Explicit ffmpeg path if not in PATH
# FFMPEG_BINARY=
# FFPROBE_BINARY=
```

## 6. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

## 7. Install remotion dependencies (optional — needed for Remotion routes)

```bash
cd remotion
npm install
cd ..
```

Verify Remotion is working:

```bash
cd remotion
npx remotion --version
cd ..
```

## 8. Check system readiness

```bash
python scripts/preflight_new_machine.py
```

This reports:
- Python version
- Backend imports (fastapi, uvicorn, dotenv)
- `.env` presence and MiniMax keys
- runtime directory writability
- ffmpeg / ffprobe availability
- Node.js / npm availability
- Remotion installation status
- Backend smoke test result

Expected output tells you which capability tier is ready:
- **UI only** — backend boots, static files served
- **Pillow route** — local-frame image composition works
- **Remotion route** — Remotion-based rendering works
- **Full TTS + video compose** — MiniMax TTS + video composition chain works

## 9. Start the backend

```bash
cd app
uvicorn main:app --reload --port 8000
```

The API is available at `http://localhost:8000`.
The Video Lab API prefix is `http://localhost:8000/video-lab`.
Static runtime assets are at `http://localhost:8000/runtime/`.

## 10. Start the frontend

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` (or the port shown in your terminal).

## 11. Verify the backend is healthy

```bash
curl http://localhost:8000/
curl http://localhost:8000/video-lab/health
```

## 12. Verify static file serving

Create a test file:

```bash
mkdir -p runtime/video_lab/experiments/test
echo "hello" > runtime/video_lab/experiments/test/manifest.json
```

访问: `http://localhost:8000/runtime/video_lab/experiments/test/manifest.json`

You should see the file content.

## 13. Open the Video Lab UI

Navigate to `http://localhost:5173/video-lab`

---

## Understanding what each route requires

| Route | Requires | Without it |
|---|---|---|
| Pillow (local_frame_compose) | ffmpeg, runtime dir | Returns HTTP 400 |
| Remotion | ffmpeg, remotion/node_modules, runtime dir | Returns HTTP 400 |
| TTS Subtitle Compose | MiniMax API key, ffmpeg, remotion | Returns HTTP 500 |
| Style Gallery Generate | MiniMax API key, all of the above | Frontend shows "缺少 final_video_url" error |

**Frontend loads successfully ≠ video generation works.** Always check the backend logs.

---

## Common Errors

### "ImportError: No module named 'fastapi'"

```bash
pip install fastapi uvicorn python-dotenv
```

### "ffmpeg not found"

Install ffmpeg:
- Windows: `winget install ffmpeg` or download from ffmpeg.org
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

### "remotion/package.json not found"

```bash
cd remotion && npm install
```

### "final_video_url / output.path" error in style gallery

This means the `/style-samples/generate` API succeeded but the backend
didn't correctly extract the video URL from the internal result object.
This is a known contract bug that was fixed in v0.8.9+.
If you see this error after updating, the backend code is older than expected.

### Backend starts but UI shows no video

1. Check browser DevTools → Network tab for the API response
2. Check backend logs for the actual `final_video_url` value
3. Verify `http://localhost:8000/runtime/` serves files correctly

### Preflight passes but generation still fails

- MiniMax keys may be wrong or expired
- ffmpeg may be in PATH but wrong version (check `ffmpeg -version`)
- Remotion may need a licensed version for certain features

---

## Runtime file locations

By default, generated files are stored under:

```
runtime/
└── video_lab/
    └── experiments/
        ├── exp_abc123/
        │   ├── final_with_audio.mp4
        │   ├── cover.png
        │   └── manifest.json
        └── ...
```

These are served statically at `/runtime/` on the backend.
