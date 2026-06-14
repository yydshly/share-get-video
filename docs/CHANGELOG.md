# Changelog

## [0.3.3.1] - 2026-06-14

### Fixed
- **requirements.txt**: Added `requests>=2.31.0` — MiniMax TTS client uses `requests` for HTTP API calls
- **tts_subtitle_compose fallback**: Subtitle burn-in failure now gracefully falls back to audio-only composition
  - `compose_av_with_subtitles` fails → `compose_video_with_audio` succeeds
  - `subtitleBurned: false`, `subtitleFallback: true` recorded in result/manifest
  - `warnings` contains "Subtitle burn-in failed... fallback to audio-only"
- **compose_video_with_audio import**: Moved to module-level import for testability

### Added
- **test_requirements_has_requests**: Verifies requirements.txt contains `requests`
- **test_tts_adapter_subtitle_fallback_still_succeeds**: Verifies fallback produces videoUrl + correct flags
- **test_tts_manifest_has_subtitle_fields**: Verifies manifest has subtitleBurned/subtitleFallback

## [0.3.3] - 2026-06-14

### Added
- **tts_subtitle_compose route**: New real route — MiniMax TTS voiceover + SRT subtitles + FFmpeg AV composition
  - `app/video_lab/providers/minimax/tts_client.py`: MiniMax TTS client (8 tests)
  - `app/video_lab/planners/voiceover_planner.py`: Template-based Chinese voiceover script generator (4 tests)
  - `app/video_lab/planners/subtitle_planner.py`: Extended with `generate_srt_from_segments()` for SRT file generation (6 tests)
  - `app/video_lab/renderers/ffmpeg_av_composer.py`: AV composer with subtitles filter (6 tests)
  - `app/video_lab/adapters/tts_subtitle_compose.py`: 9-step adapter (5 tests)
  - `.env.example`: MiniMax TTS environment variables
- **RouteScorePanel manual route scoring**: `scoreableStatuses = ["succeeded", "manual"]` — manual routes now show scoring UI
- **_build_warnings for manual_completed**: Returns `[]` for `status == "manual_completed"`, no misleading warning shown
- **RouteResultCard manual route explanation**: Shows purple explanation text for manual routes
- **RouteResultCard audio/subtitle links**: Shows 🔊 播放音频 and 📝 打开字幕 links for TTS routes

### Changed
- **tts_subtitle_compose registry**: Status changed from `mock` to `real`, adapter_category set, pipeline updated to 9 steps
- **README.md**: Updated route table to include tts_subtitle_compose and hyperframes_html_render

### Fixed
- **test_route_benchmark.py**: Updated mock route test to use `ai_asset_then_compose` (tts_subtitle_compose is now real)

### Docs
- **docs/TTS_SUBTITLE_ROUTE_V0.3.3.md**: New documentation for TTS subtitle route

## [0.3.2.1] - 2026-06-14

### Fixed
- **RouteScorePanel manual route scoring**: `scoreableStatuses = ["succeeded", "manual"]` — manual routes now show scoring UI
- **_build_warnings for manual_completed**: Returns `[]` for `status == "manual_completed"`, no misleading warning shown
- **RouteResultCard manual route explanation**: Shows purple explanation text "该路线已生成 HTML → 手动用 HyperFrames 渲染后再评分"
- **manual route non-scoreable message**: Shows appropriate message per status (failed/mock/reserved)

### Added
- **test_route_benchmark_runs_hyperframes_route**: Verifies no warnings for manual route
- **test_build_warnings_empty_for_manual_completed**: Verifies `_build_warnings` returns [] for manual_completed

### Docs
- **HYPERFRAMES_ROUTE_V0.3.2.md**: Added V0.3.2.1 section documenting manual route scoring and verification status

## [0.3.2] - 2026-06-14

### Added
- **hyperframes_html_render route**: New manual route — generates self-contained HTML file for HeyGen HyperFrames plugin
  - `app/video_lab/renderers/hyperframes/html_builder.py`: Generates portrait 9:16 HTML with CSS animations
  - `app/video_lab/adapters/hyperframes_html_render.py`: 5-step adapter
  - Registry: `status="manual"`, `route_id="hyperframes_html_render"`
  - Runner: `manual` status handled separately, no videoUrl expected
  - `BenchmarkRunner._execute_route`: manual branch that executes adapter and returns manual status
  - `BenchmarkRunner`: overall status check updated to treat manual as terminal
- **RouteResultCard**: Shows "打开生成的 HTML" link for manual routes
- **RouteResult.manual status**: TypeScript type updated, STATUS_COLORS updated
- **HyperFrames HTML**: 7.6KB self-contained HTML with dark theme, CSS keyframe animations, auto-page navigation

### Changed
- **RouteBenchmark.count check**: `all(r.status in ("mock", "reserved")` → `("mock", "reserved", "manual")`

### Fixed
- **FFmpeg concat file paths**: `build_concat_file_content()` uses `Path.resolve().as_posix()` for absolute paths
- **FFmpeg cwd dependency removed**: Both compose functions use absolute paths throughout
- **RouteResult warnings**: `_build_warnings()` preserves FFmpeg/render failure reasons
- **Remotion `USE_SHELL` constant**: `shell=True` only on Windows (`os.name == "nt"`)
- **FFmpeg failure tests**: Patched `check_ffmpeg_available` at both import locations

### Git
- `.gitignore`: `remotion/src/props.json` and `remotion/out/`
- `remotion/package-lock.json` committed

## [0.3.1.2] - 2026-06-14

### Fixed
- **FFmpeg concat file paths**: `build_concat_file_content()` now uses `Path.resolve().as_posix()` for absolute paths (was using relative paths causing FFmpeg to fail with "No such file")
- **FFmpeg cwd dependency removed**: Both `compose_video_from_frames` and `compose_video_from_frame_sequence` now use absolute paths throughout — no longer rely on `cwd`
- **RouteResult warnings**: `_build_warnings()` helper preserves FFmpeg/render failure reasons in `warnings` field for UI display
- **Remotion `USE_SHELL` constant**: `shell=True` only on Windows (`os.name == "nt"`), defined as module-level `USE_SHELL` constant

### Added
- **Gitignore**: `remotion/src/props.json` and `remotion/out/` added to `.gitignore`
- **remotion/package-lock.json**: Committed to repo for reproducible environments

### Verified
- **local_frame_compose + template_programmatic_render**: Both routes now succeed in Route Benchmark simultaneously
- **benchmarkId**: `bench_c673f651e32d` — `completed` status, both routes `succeeded`

## [0.3.1.1] - 2026-06-14

### Fixed
- **Remotion CLI path**: `REMOTION_ROOT_TSX` changed from `remotion/src/Root.tsx` to `src/Root.tsx` (relative to `cwd=remotion`)
- **Props path**: `--props` now uses `./src/props.json` prefix for Windows compatibility
- **output.mp4**: Now uses `resolve()` absolute path to avoid cwd confusion
- **shell=True for subprocess**: Added `shell=True` to `subprocess.run` for Windows (`npx` is `npx.cmd`)
- **Root.tsx**: Rewritten to use standard `Composition` pattern with `registerRoot`
- **manifestUrl writing order**: Fixed adapter to compute `manifest_url` BEFORE building manifest dict
- **Renderer manifest**: `remotion_renderer.py` now writes `manifestUrl` into the manifest file

### Verified
- **Remotion真实渲染**: Successfully rendered MP4 via `npx remotion render` (2.8MB, 45s video)
- **Chrome headless**: Remotion downloads and uses `chrome-headless-shell` automatically

## [0.3.1] - 2026-06-14

### Added
- **Remotion workspace** (`remotion/`): New Node.js workspace for Remotion/React video rendering
  - `package.json`: @remotion/cli, @remotion/renderer, react
  - `src/AiNewsVideo.tsx`: Portrait 9:16 template with cover, keypoint cards, summary pages
  - `src/Root.tsx`: Remotion entry point
  - `src/data.ts`: Props types + defaults
- **Remotion backend renderers** (`app/video_lab/renderers/remotion/`):
  - `props_builder.py`: Builds Remotion props JSON from structured content
  - `remotion_renderer.py`: Executes `npx remotion render` via subprocess
- **remotion_template adapter** (`adapters/remotion_template.py`): Real implementation with 7-step pipeline
- **Route benchmark**: `template_programmatic_render` is now `real` (was `mock`)
- **Frontend RouteResultCard**: Now shows `expectedPipeline` artifact for mock/reserved routes, manifest link for real routes

### Changed
- **template_programmatic_render route**: Status changed from `mock` to `real`
- **BenchmarkRunner**: `template_programmatic_render` now executes real adapter; metrics updated to `estimated_cost=low-medium`, `stability=medium`, `quality_ceiling=high`
- **test_video_lab.py**: `test_experiment_with_ai_frontier_and_template_renders_12_steps` → `test_experiment_with_ai_frontier_and_template_renders_7_steps` (adapter now has 7 steps, not 12)

### Fixed
- **RouteResultCard**: TypeScript errors on `pipeline`/`note` properties resolved with proper `ArtifactEntry` type alias

## [0.3.0] - 2026-06-14

### Added
- **routes_benchmark module**: New module for multi-route horizontal verification (`app/video_lab/routes_benchmark/`)
  - `models.py`: `RouteBenchmark`, `RouteResult`, `RouteMetrics` dataclasses
  - `registry.py`: Route registry with 6 registered routes
  - `runner.py`: `BenchmarkRunner` to execute benchmarks across routes
- **GET /video-lab/routes**: New API endpoint to list all registered routes
- **POST /video-lab/route-benchmarks**: New API to create and run multi-route benchmarks
- **GET /video-lab/route-benchmarks/{id}**: New API to retrieve benchmark results
- **RouteBenchmarkPage.tsx**: New frontend page for route benchmarking (`/video-lab/route-benchmark`)
- **RouteScorePanel.tsx**: New component for scoring routes across 8 dimensions
- **Homepage navigation**: Added "多路线验证" card linking to `/video-lab/route-benchmark`
- **types/index.ts**: Added `RouteDefinition`, `RouteResult`, `RouteBenchmark`, `RouteMetrics` types
- **schemas.py**: Added `CreateBenchmarkRequest` for POST /route-benchmarks

### Changed
- **renderer keyPoints fallback**: `generate_frames()` now reads `keyPoints` first, falls back to `key_points`, then empty list
- **local_frame_compose**: Remains the only `real` route in the benchmark framework

## [0.2.5.1] - 2026-06-14

### Fixed
- **P0 keyPoints field mismatch**: Renderer now reads `key_points` from adapter (backward compat key added), and no longer pads/truncates to fake the count
- **P1 includeOverview/includeSummary**: Now wired from render_params to `generate_frames()` - conditional frame generation works correctly
- **P1 aspectRatio=1:1**: Added `resolve_resolution()` helper, 1:1 now correctly maps to 1080x1080 (was falling through to 1920x1080)
- **P1 sample script dependency**: Replaced `requests` with standard library `urllib` - no external dependency needed
- **Warning messages**: Invalid highlightMode/stylePreset warnings now show original illegal value instead of fallback value

### Changed
- **generate_frames()**: Signature updated to accept `include_overview` and `include_summary` parameters
- **local_frame_compose.py**: Now passes `include_overview`/`include_summary` to renderer and records them in manifest/assets/step10 keyData
- **render_params.py**: Added `resolve_resolution()` function and fixed warning message templates

## [0.2.5] - 2026-06-14

### Added
- **render_params.py**: New module with `LocalFrameRenderParams` dataclass and `parse_local_frame_params()` for parameter validation
- **Frontend parameter panel**: New "生成参数" section in VideoExperimentPage for `method_local_frame_compose`
- **TemplateReviewPanel**: New component showing template acceptance suggestions based on evaluation scores
- **templateReview.ts**: Domain logic for template review based on result and evaluation
- **generate_ai_frontier_sample.py**: Sample generation script using recommended parameters
- **SAMPLE_ACCEPTANCE_V0.2.5.md**: Sample acceptance documentation
- **LOCAL_FRAME_VISUAL_PRESET_V0.2.4.md**: Visual preset documentation

### Changed
- **local_frame_compose.py**: Now parses and uses render_params, records renderParams in manifest/assets/rawOutput
- **Step 3**: Now respects keyPointCount and records requestedKeyPointCount/actualKeyPointCount
- **highlightMode support**: Added `extract_highlights_by_mode()` with auto/numbers/none modes
- **VideoExperimentDetailPage**: Now displays render params and TemplateReviewPanel

## [0.2.4.1] - 2026-06-14

### Fixed
- **transition_composer.py**: Replaced pixel-by-pixel Python loop in `generate_fade_frames()` with Pillow's native `Image.blend()` for significant performance improvement on 1080x1920 frames
- **FFmpeg composition order**: FFmpeg now uses `frameSequence` order instead of `duration_per_frame` dict ordering, ensuring transition frames are properly inserted between main frames

### Added
- **ffmpeg_composer.py**: Added `compose_video_from_frame_sequence()` function for sequence-aware video composition
- **ffmpeg_composer.py**: Added `build_concat_file_content()` helper function for generating concat demuxer file content
- **local_frame_renderer.py**: Now returns `frameSequence` (ordered list of all frames) and `durationByPath` (path-keyed duration dict)
- **manifest/assets**: Added `frameSequenceCount` and `transitionOrderApplied` fields
- **Step 11 keyData**: Now includes `frameSequenceCount` and `transitionOrderApplied`

### Changed
- **build_frame_sequence_with_transitions()**: Now accepts `main_durations` parameter to preserve real main frame durations through transition sequence
- **local_frame_compose.py**: Now prioritizes `frameSequence`-based composition when available, falls back to original method otherwise

## [0.2.4] - 2026-06-14

### Added
- **visual_theme.py**: New module defining AI Frontier Dark preset - colors, typography (font sizes), spacing, shadows, category colors, and blend utilities
- **frame_templates.py**: New module with template functions for cover, overview, keypoint, and summary frames using Pillow
- **transition_composer.py**: New module for fade transitions - generates intermediate Pillow frames between main frames
- **text_layout.py enhancements**: Added `extract_highlights()`, `split_lines_with_max_count()`, `fit_font_size()`, `wrap_text_by_visual_width()` functions

### Changed
- **local_frame_renderer.py**: Upgraded to use AI Frontier Dark visual templates with enhanced cover, new overview frame, improved keypoint frames with category tags and highlight support, and optimized summary frame
- **local_frame_compose.py**: Manifest and assets now include `visualPreset`, `templateVersion`, `transitionEnabled`, `transitionType`, `transitionFrames`, and `highlightTerms` fields
- **EvaluationPanel.tsx**: Fixed opacity bug - save button now correctly uses `!allRated` instead of checking if all scores are 0
- **Cover template**: Now includes top label ("AI Frontier Radar"), subtitle, 3 signal tags, decorative elements, date, and footer
- **Overview template**: New frame type showing top 4 key points with indices (V0.2.4 new)
- **Keypoint template**: Enhanced with category tag, title with highlight support, body with highlight extraction, and improved layout
- **Summary template**: Now includes numbered conclusions and CTA section

### Fixed
- **text_layout.py**: Enhanced Chinese text wrapping with better visual width estimation and line count limiting

## [0.2.3.1] - 2026-06-14

### Fixed
- **Artifact URLs**: `frame_image`, `cover_image`, `video_output` artifacts now include `url` field in payload (`path_to_url`-derived) so ArtifactViewer can preview in browser
- **manifestUrl in file**: `manifestUrl` is now computed before `write_manifest()` is called, so the actual `manifest.json` file on disk contains the field
- **EvaluationPanel validation**: Save button now requires all 7 dimensions to be rated (1–5) before enabling; partial submissions are blocked client-side with a hint message

## [0.2.3] - 2026-06-14

### Added
- **Experiment Detail Page**: New `/video-lab/experiments/:id` page showing full experiment details including video preview, cover, assets, steps timeline, artifacts list, experiment summary, and evaluation panel
- **ArtifactViewer Component**: Reusable component for displaying artifacts — handles `video_output`, `cover_image`, `frame_image`, `manifest`, and other artifact types with preview and download links
- **ProductionStepsTimeline Component**: Reusable timeline component for production steps — shows status, input/output summaries, keyData, artifacts, and logs; uses ArtifactViewer internally
- **EvaluationPanel Component**: Human evaluation form with star ratings (1-5) across 7 dimensions (informationAccuracy, readability, visualQuality, pacing, shareability, stability, productizationValue) + notes; saves via POST /experiments/{id}/evaluation
- **ExperimentSummaryPanel Component**: Auto-generated experiment conclusion based on result + evaluation — shows recommendation badge (高/中/低), strengths, problems, and next steps
- **VideoExperimentEvaluation Model**: New evaluation model in `models.py` with 7 dimensions and `averageScore()` method
- **Evaluation API**: `POST /video-lab/experiments/{id}/evaluation` and `GET /video-lab/experiments/{id}/evaluation` endpoints
- **ExperimentRunner evaluation storage**: `save_evaluation()` and `get_evaluation()` methods
- **manifestUrl**: Added `manifestUrl` field to `manifest.json` payload for direct download
- **Compare Page**: Enhanced with frame count, resolution, FFmpeg status, productization badge, "查看详情" button per card

### Changed
- **Frontend routing**: Added `/video-lab/experiments/:id` route for experiment detail page
- **Frontend error handling**: Improved error display in experiment creation page

## [0.2.2] - 2026-06-14

### Fixed
- **POST /video-lab/experiments**: Changed from implicit query parameters to explicit JSON body with `CreateExperimentRequest` Pydantic schema — frontend JSON body now matches the API contract, eliminating 422 errors on real page requests
- **API error responses**: `ValueError` (unknown test case / method) now raises `HTTPException(400)` instead of returning 200 with error field; unexpected exceptions raise `HTTPException(500)`; malformed request body returns FastAPI 422
- **Frontend error handling**: `handleRun()` now checks `resp.ok` before parsing JSON and surfaces HTTP status + detail message clearly

### Added
- **`app/video_lab/schemas.py`**: New `CreateExperimentRequest` Pydantic model with `testCaseId`, `methodId`, `title`, `inputPayload`, `params`
- **`tests/test_video_lab_api.py`**: 12 new API integration tests covering JSON body success, 422 for missing fields, 400 for unknown test case / method, business failure distinction (200 + failed status), and health / list / get endpoints

### Changed
- **API contract**: Unknown `testCaseId` → HTTP 400; unknown `methodId` → HTTP 400; malformed body → HTTP 422; server error → HTTP 500; experiment business failure (e.g. FFmpeg unavailable) → HTTP 200 with `experiment.status = "failed"`

## [0.2.1] - 2026-06-14

### Fixed
- **path_to_url()**: Corrected URL generation to preserve `/runtime/video_lab/experiments/` prefix — previously stripped too much path, causing 404 on video preview
- **ExperimentRunner status**: FFmpeg failure now correctly sets `experiment.status = failed` instead of unconditionally marking as `succeeded`
- **FFmpeg failure detection**: Added `_result_has_failed_steps()` and `_result_declares_failure()` checks covering `productionSteps`, `rawOutput.status`, `productizationRecommendation`, and `ffmpegSuccess`

### Changed
- **ArtifactType**: Added `video_output`, `cover_image`, `frame_image`, `manifest` types; `local_frame_compose` output MP4 now uses `video_output` instead of `mock_video`
- **frontend API_BASE**: Now reads from `VITE_API_BASE` environment variable with fallback to `http://localhost:8000/video-lab`
- **manifest**: Now includes `ffmpegCommand` and `ffmpegMessage` fields for debugging
- **Step 11 keyData**: Now exposes `ffmpegCommand` and `ffmpegMessage` for log inspection

### Added
- **frontend/.env.example**: Documents `VITE_API_BASE` configuration
- **ArtifactType frontend types**: TypeScript `ArtifactType` now includes `video_output`, `cover_image`, `frame_image`, `manifest`

## [0.2.0] - 2026-06-14

### Added
- **renderers**: New `renderers/` module with `local_frame_renderer.py`, `ffmpeg_composer.py`, `file_store.py`, `text_layout.py`
- **local_frame_compose**: Upgraded from mock to real rendering - generates PNG frames with Pillow, composites MP4 with FFmpeg
- **Pillow rendering**: Deep gradient backgrounds, centered Chinese text, info card frames with index/title/body/source
- **FFmpeg composition**: concat demuxer-based frame sequence → MP4 at 1080x1920 30fps
- **Static file serving**: `/runtime` mounted for accessing generated video files
- **frontend**: Auto-fill default input when selecting case, video preview with controls, download links, enhanced artifact details
- **tests**: 12 new tests in `test_video_lab_local_frame.py`
- **requirements.txt**: Added Pillow dependency
- **.gitignore**: Updated to ignore `runtime/` and video/audio file formats

### Changed
- `local_frame_compose` adapter now produces real MP4 output (if FFmpeg available)
- FastAPI version bumped to 0.2.0

## [0.1.1] - 2026-06-14

### Added
- **docs**: 新增架构文档、技术路线矩阵、开发流程、已知限制、路线图、变更日志
- **test case**: 新增 `case_ai_frontier_daily_001` (今日 AI 前沿共享短视频)
- **data structures**: 新增 `VideoProductionStep` 和 `VideoProductionArtifact` 数据结构
- **planners**: 新增 `content_structurer`, `key_point_extractor`, `script_planner`, `storyboard_planner`, `asset_planner`, `render_planner` 模块
- **adapters**: 增强所有 adapter 返回 12 步骤 + artifacts (script, storyboard, subtitle_plan, voiceover_plan, asset_plan, render_plan, mock_video)
- **advisor**: 新增 `case_ai_frontier_daily_001` 推荐规则
- **UI**: 增强实验执行页展示 Production Steps Timeline；增强对比页展示关键风险和产品化判断；首页补充第一目标说明
- **tests**: 新增 8 个测试（case_ai_frontier_daily_001 存在性、12 步骤验证、artifact 验证、adapter 差异验证、架构边界测试）

### Changed
- **README**: 补充完整项目说明、启动方式、测试命令、分支规范

## [0.1.0] - 2026-06-14

### Added
- **core models**: VideoTestCase, VideoMethod, VideoExperiment, VideoExperimentResult, VideoEvaluation, VideoMethodAdvice
- **seed data**: 6 个测试用例，6 类生成方案
- **method registry**: 6 个 adapter (local_frame_compose, local_media_compose, template_programmatic_render, ai_video_direct, ai_asset_then_compose, hybrid_pipeline)
- **advisor**: 静态推荐规则（5 个场景）
- **experiment runner**: 完整的实验创建→执行→结果流程
- **FastAPI router**: `/video-lab/*` API 端点
- **React frontend**: 5 个页面（Home, Test Cases, Methods, Experiments, Compare, Advice）
- **tests**: 13 个后端测试
