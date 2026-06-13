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

### V0.2.1 下一阶段优化
- 卡片设计优化
- 简单转场
- 背景渐变/粒子/动态感
- 更好的中文排版
- 下载/分享页
- 评分面板

---

## V0.3 - Remotion 模板渲染真实 MP4

**目标**
- 接入 Node.js + Remotion CLI
- 实现 `run_remotion_template()` 调用真实渲染
- 验证 Remotion 渲染质量

### 里程碑
- [ ] 验证 Node.js 环境
- [ ] 创建第一个 Remotion 模板组件
- [ ] 实现 `run_remotion_template()` 调用 `npx remotion render`
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
