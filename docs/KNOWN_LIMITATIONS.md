# Known Limitations

## 当前 V0.3.2 已知限制

### 1. 部分 Adapter 已升级为真实渲染

- `local_frame_compose` - **已支持真实渲染**（Pillow + FFmpeg）
- `template_programmatic_render` - **已支持真实渲染**（Remotion/React 模板）
- `hyperframes_html_render` - **manual 状态**（生成 HTML artifact，需人工复制到 HeyGen HyperFrames 插件渲染）
- `local_media_compose` - 返回模拟数据，不调用 FFmpeg
- `ai_video_direct` - Reserved 状态，无 API 接入
- `ai_asset_then_compose` - 返回模拟数据，不调用 LLM/TTS/图像生成
- `hybrid_pipeline` - 返回模拟数据，无真实路由引擎
- `tts_subtitle_compose` - 返回模拟数据，不调用 TTS API

### 2. FFmpeg 必须可用

- `local_frame_compose` 依赖 FFmpeg 进行视频合成
- FFmpeg 不可用时，视频合成步骤会失败（`step.status = failed`），实验整体状态为 `failed`

### 3. Remotion 需要 Node.js 环境

- `template_programmatic_render` 依赖 `npx remotion` CLI
- 环境不可用时 route 返回 `failed`，其他路线不受影响
- 安装方式: `cd remotion && npm install`
- **V0.3.1.1 已验证真实渲染**（2.8MB MP4，45s，1080x1920）

### 4. 无数据库

- 实验结果和人工评分均存储在后端内存中（ExperimentRunner 单例）
- 服务重启后数据丢失
- 对比页依赖 localStorage 缓存（后端内存丢失后 localStorage 中的索引仍存在，但关联数据已不可用）
- 所有配置（test cases、methods）来自 seed_data.py，无动态增删改

### 5. TTS 未接入

- 旁白生成依赖 TTS API
- 当前只有 placeholder
- 计划在 V0.3.2 接入 MiniMax TTS

### 6. Remotion 模板为最小验证版

- V0.3.1.1 Remotion 模板不做最终视觉追求
- 仅 Cover + KeyPoint Cards + Summary 三个基本页面
- 无 TTS、无 AI 图片、无复杂动画
- 计划在后续版本中优化视觉质量

### 7. 无批量实验功能

- 每次只能运行一个实验
- 无法并行对比多个 method

### 8. 无自动化评分

- VideoExperimentEvaluation 评分需要人工输入
- 无 LLM 自动评分

### 9. runtime 产物不提交 Git

- `runtime/experiments/` 下的视频、图片、manifest 等为运行时产物
- 不应提交到 Git 仓库（已通过 `.gitignore` 排除）
- 每次实验生成独立的 experiment_id 子目录

## 后续解除计划

| 限制 | 解除版本 | 解除方式 |
|------|---------|---------|
| local_frame_compose | V0.2 ✅ | Pillow + FFmpeg |
| 模板参数化 | V0.2.5 ✅ | render_params.py |
| Remotion 渲染 | V0.3.1.1 ✅ | remotion workspace + npx remotion render + shell=True fix |
| TTS 接入 | V0.3.2 | MiniMax TTS API |
| AI 视频接入 | V0.4 | 接入 Runway/Kling 等 API |
| LLM/TTS/图像 | V0.5 | 接入 OpenAI/ElevenLabs/DALL-E |
| 持久化存储 | V0.6 | 引入 SQLite 或 PostgreSQL |
| 批量实验 | V0.6 | 并行实验调度器 |
| 自动评分 | V0.6 | LLM-as-Judge 评分模块 |
