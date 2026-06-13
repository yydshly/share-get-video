# Changelog

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
