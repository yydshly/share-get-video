# Video Capability Lab Roadmap

## 愿景

构建一个可扩展的视频生成能力验证平台，通过统一测试场景系统化评估不同技术路线的**效果、成本、稳定性、可控性和产品化价值**，最终找到最适合特定场景的方案组合。

---

## V0.1 - 架构骨架 ✅

**完成时间**：2026-06-14

### 目标
- 建立核心数据模型（VideoTestCase, VideoMethod, VideoExperiment, VideoExperimentResult, VideoEvaluation, VideoMethodAdvice）
- 实现 6 类技术路线（local_frame_compose, local_media_compose, template_programmatic_render, ai_video_direct, ai_asset_then_compose, hybrid_pipeline）
- 实现 Method Registry + Adapter 分层
- 实现静态 Advisor 规则
- 6 个内置测试用例
- 5 个 UI 页面
- 13 个后端测试

### 状态
- ✅ 后端架构完成
- ✅ 前端 UI 骨架完成
- ✅ 测试覆盖核心配置
- ❌ 无真实视频生成能力

---

## V0.1.1 - 架构补强 + 主场景深化 ✅

**完成时间**：2026-06-14

### 目标
- 文档归档（README, docs/）
- 新增 AI 前沿日报共享视频测试用例 (case_ai_frontier_daily_001)
- Production Steps + Artifacts 数据结构
- Planner 模块（script, storyboard, asset, render）
- 增强 Adapter 返回 12 步骤 + artifacts
- UI 增强（步骤时间线、风险展示、产品化判断）

### 状态
- ✅ 文档完成
- ✅ 新测试用例完成
- ✅ Production Steps 数据结构完成
- ✅ Planner 模块完成
- ✅ Adapter 12 步骤完成
- ✅ UI 增强完成

---

## V0.2 - 本地帧合成 + FFmpeg 真实 MP4 ✅

**目标**
输入 `case_ai_frontier_daily_001` → 生成真实封面帧 → 生成多张信息卡片帧 → FFmpeg 合成 30-45 秒 MP4 → 页面预览

### 里程碑
- [x] 实现 `run_local_frame_compose()` 调用真实 Pillow 生成帧
- [x] 实现 FFmpeg 合成真实 MP4
- [x] 支持 9:16 竖屏输出
- [x] 支持字幕 burn-in
- [x] 实验结果可下载

### 验收标准
- 运行 `case_ai_frontier_daily_001` + `local_frame_compose`
- 输出真实 MP4 文件（可播放）
- 时长 30-45 秒
- 包含信息卡片和字幕

---

## V0.2.4 - 本地视频视觉质量优化 ✅

**完成时间**：2026-06-14

### 目标
把"能生成真实 MP4"提升为"视频观感基本可分享"

### 新增模块
- `visual_theme.py`: AI Frontier Dark 视觉主题定义
- `frame_templates.py`: 封面、概览、信号卡片、总结模板
- `transition_composer.py`: Fade 转场中间帧生成

### 增强功能
- **封面模板**: 大标题、副标题、3个信号 tag、背景渐变、装饰元素
- **概览帧 (Overview)**: 显示前4条重点内容索引
- **信号卡片**: 分类标签、重点数字高亮、中文排版优化
- **总结帧**: 结论列表 + CTA
- **Fade 转场**: Pillow 中间帧实现平滑过渡
- **高亮提取**: 自动识别百分比、倍数、大数字

### V0.2.4 下一阶段优化 (V0.2.5)
- 用 case_ai_frontier_daily_001 生成真实样例
- 人工评分记录
- 根据评分调整模板参数
- 支持 stylePreset 参数化
- 支持 duration / keyPointCount / highlightMode 参数
- 固化可复用的 AI 资讯分享视频模板

---

## V0.2.4.1 - Fade 转场顺序与性能修复 ✅

**完成时间**：2026-06-14

### 问题修复
- Fade 转场帧生成顺序错误（V0.2.4 中 fade 帧在主帧之后而非之间）
- 大量关键点时帧生成性能问题

### 修复内容
- `transition_composer.py`: 修正 `build_frame_sequence_with_transitions` 中的顺序逻辑
- `local_frame_renderer.py`: 直接传入真实 `main_durations` 而非估算值
- `compose_video_from_frame_sequence`: 优先使用 frameSequence 路径
- FFmpeg concat 顺序现在与视觉顺序一致

---

## V0.2.5 - 模板参数化 + 样例验收 ✅

**完成时间**：2026-06-14

### 目标
把 `local_frame_compose` 从固定模板能力升级为可配置、可复验、可验收的 AI 资讯分享视频模板。

### 新增功能
- **参数化模型** (`render_params.py`): `LocalFrameRenderParams` dataclass + `parse_local_frame_params()`
- **keyPointCount 支持**: 截断或补齐关键点列表
- **highlightMode 支持**: `auto` / `numbers` / `none` 三种模式
- **transition 参数支持**: `transitionEnabled` + `transitionFrames`
- **前端参数面板**: 实验创建页新增「生成参数」区域
- **详情页参数展示**: 展示所有生成参数
- **模板验收建议**: `TemplateReviewPanel` + `buildTemplateReview()`
- **样例脚本**: `scripts/generate_ai_frontier_sample.py`

### 推荐参数
```json
{
  "targetDuration": 45,
  "aspectRatio": "9:16",
  "keyPointCount": 6,
  "highlightMode": "auto",
  "transitionEnabled": true,
  "transitionFrames": 4,
  "stylePreset": "ai_frontier_dark"
}
```

### V0.2.5 下一阶段优化 (V0.2.6)
- 运行真实样例
- 人工给分
- 根据评分调整参数
- 固化推荐参数
- 决定是否进入 V0.3 Remotion 方案评估

---

## V0.3 - Remotion 最小真实路线验证

**目标**
- 接入 Node.js + Remotion CLI
- 实现 `run_remotion_template()` 调用真实渲染
- 同一份 case_ai_frontier_daily_001 → Remotion 模板 → MP4 → 回填 Route Benchmark
- 和 local_frame_compose 横向对比

### V0.3.0 已完成
- **多路线横向验证框架**（Route Benchmark）
  - `routes_benchmark/` 模块（models, registry, runner）
  - GET /routes, POST /route-benchmarks, GET /route-benchmarks/{id} API
  - RouteBenchmarkPage 前端页面 + RouteScorePanel 评分组件
  - local_frame_compose 是当前唯一 real 路线

### V0.3.1 待完成
- [ ] 验证 Node.js 环境
- [ ] 创建第一个 Remotion 模板组件
- [ ] 实现 `run_remotion_template()` 调用 `npx remotion render`
- [ ] Remotion 作为 real route 接入 Route Benchmark
- [ ] 对比 FFmpeg 输出 vs Remotion 输出

---

## V0.4 - 接入视频模型 Adapter

**目标**
- 选定一个视频模型提供商（Runway / Kling / Pika / Sora）
- 实现 `run_ai_video_direct()` 调用真实 API
- 评估 AI 视频在 AI 资讯场景的可行性

### 里程碑
- [ ] API 凭证配置
- [ ] 实现 `run_ai_video_direct()` 调用
- [ ] 评估字幕可控性
- [ ] 评估批量一致性

---

## V0.5 - LLM 拆脚本 + TTS + 图片生成 + 合成

**目标**
- 实现 `ai_asset_then_compose` 真实调用
- LLM 生成脚本和旁白
- TTS 生成语音
- 图像模型生成封面和背景素材
- Remotion/FFmpeg 最终合成

### 里程碑
- [ ] LLM 脚本拆分模块
- [ ] TTS 旁白生成
- [ ] 图像生成封面
- [ ] 全流程串联

---

## V0.6 - 批量对比实验 + 产品化报告

**目标**
- 引入数据库持久化
- 批量并行实验调度
- LLM-as-Judge 自动评分
- 产品化可行性报告生成

### 里程碑
- [ ] 数据库集成（SQLite/PostgreSQL）
- [ ] 批量实验 runner
- [ ] 自动评分模块
- [ ] PDF/HTML 报告导出
