# Remotion Route V0.3.1 - Minimum Verification

## Overview

V0.3.1 upgrades `template_programmatic_render` from mock to real route. The route now renders real MP4 videos using Remotion/React.

## Architecture

```
input_payload.content
    ↓
structure_content (planner)
    ↓
extract_key_points (planner)
    ↓
build_remotion_props (props_builder.py)
    ↓
npx remotion render (remotion_renderer.py)
    ↓
manifest.json
    ↓
VideoExperimentResult
```

## Components

### Remotion Workspace (`remotion/`)

```
remotion/
├── package.json      # @remotion/cli, @remotion/renderer, react
├── tsconfig.json
└── src/
    ├── Root.tsx          # registerRoot(AiNewsVideo)
    ├── AiNewsVideo.tsx   # Main composition
    └── data.ts           # AiNewsVideoProps type + defaultProps
```

### Backend Renderers (`app/video_lab/renderers/remotion/`)

- **props_builder.py** - Builds `{title, subtitle, keyPoints, durationSec, stylePreset}` JSON from structured content
- **remotion_renderer.py** - Runs `npx remotion render` via subprocess; returns `{success, videoUrl, manifestUrl, logs, warnings}`

### Adapter (`app/video_lab/adapters/remotion_template.py`)

Real implementation with 7 production steps:
1. Receive Input
2. Structure Content
3. Extract Key Points
4. Build Remotion Props
5. Check Remotion Environment
6. Run Remotion Render
7. Generate Conclusion

## Remotion Template: AiNewsVideo

Portrait 9:16 (1080x1920), 30fps.

### Pages
1. **Cover Page** - Title with fade-in animation, accent glow, decorative line
2. **KeyPoint Cards** (N pages) - Each key point gets its own card with index badge, title, body, source
3. **Summary Page** - Bulleted list of all key points

### Animation
- CSS opacity + translateY spring entrance
- Subtle border pulse on cards
- Staggered text reveals

### Style Preset: `ai_frontier_dark`
- Background: `#0a0e1a`
- Card surface: `#1a2236`
- Accent: `#3b82f6` / `#8b5cf6`
- Text: `#f8fafc` / `#94a3b8`

## Usage

### Setup

```bash
cd remotion && npm install
```

### Render manually

```bash
cd remotion
npx remotion render src/Root.tsx AiNewsVideo out/video.mp4 \
  --props=src/props.json --codec=h264
```

### Via Route Benchmark

1. Open `/video-lab/route-benchmark`
2. Select `local_frame_compose` + `template_programmatic_render`
3. Run benchmark
4. Both routes show real videoUrl

## Graceful Degradation

If Remotion environment is unavailable:
- Route returns `status=failed`
- `warnings` contains: `"Remotion not installed. Run: cd remotion && npm install."`
- Other routes continue to work

## Metrics

| Route | Estimated Cost | Stability | Quality Ceiling |
|-------|---------------|-----------|-----------------|
| local_frame_compose | low-medium | high | medium |
| template_programmatic_render | low-medium | medium | high |

## Limitations (V0.3.1)

- Minimum verification only — not a final visual template
- No TTS / voiceover
- No AI-generated images
- No AI video generation
- No complex semantic rewriting layer
- Single style preset (`ai_frontier_dark`)
- No audio track

## Next: V0.3.2

MiniMax TTS + subtitle route verification — same content, add voiceover and subtitle synthesis.
