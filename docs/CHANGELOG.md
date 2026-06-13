# Changelog

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
