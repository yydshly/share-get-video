# Known Limitations

## 当前 V0.1.1 已知限制

### 1. 所有 Adapter 均为 Mock 状态

- `local_frame_compose` - 返回模拟数据，不生成真实帧
- `local_media_compose` - 返回模拟数据，不调用 FFmpeg
- `template_programmatic_render` - 返回模拟数据，不调用 Remotion
- `ai_video_direct` - Reserved 状态，无 API 接入
- `ai_asset_then_compose` - 返回模拟数据，不调用 LLM/TTS/图像生成
- `hybrid_pipeline` - 返回模拟数据，无真实路由引擎

### 2. 无持久化存储

- 实验结果存储在内存中（ExperimentRunner 单例）
- 页面刷新后数据丢失
- 对比页依赖 localStorage

### 3. 无数据库

- 所有配置（test cases、methods）来自 seed_data.py
- 无动态增删改

### 4. ai_video_direct 为 Reserved

- video model API 未接入
- 暂无模型提供商配置
- 无法评估真实生成效果

### 5. Remotion 需要 Node.js 环境

- Remotion 渲染依赖 `npx remotion` CLI
- 当前环境未安装 Node.js
- V0.3 才能打通真实渲染

### 6. TTS 未接入

- 旁白生成依赖 TTS API
- 当前只有 placeholder

### 7. 无批量实验功能

- 每次只能运行一个实验
- 无法并行对比多个 method

### 8. 无自动化评分

- VideoEvaluation 评分需要人工输入
- 无 LLM 自动评分

### 9. 前端无真实 API 调用

- 实验执行页依赖后端 API
- 但如果后端未启动，UI 仍可展示（静态数据）

## 后续解除计划

| 限制 | 解除版本 | 解除方式 |
|------|---------|---------|
| Mock adapter | V0.2 | 实现 local_frame_compose + FFmpeg |
| Remotion 渲染 | V0.3 | 接入 Node.js + Remotion CLI |
| AI 视频接入 | V0.4 | 接入 Runway/Kling 等 API |
| LLM/TTS/图像 | V0.5 | 接入 OpenAI/ElevenLabs/DALL-E |
| 持久化存储 | V0.6 | 引入 SQLite 或 PostgreSQL |
| 批量实验 | V0.6 | 并行实验调度器 |
| 自动评分 | V0.6 | LLM-as-Judge 评分模块 |
