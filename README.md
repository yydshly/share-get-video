# Video Capability Lab

> 视频生成能力验证平台

## 产品定位

Video Capability Lab 是一个**视频生成能力验证平台**，不是"一键视频生成器"。

核心目标：用统一测试场景验证不同视频生成技术路线的**效果、成本、稳定性、可控性和产品化价值**。

## 第一目标

**AI 信息获取后的共享视频制作能力验证**

当前优先场景：AI 资讯共享短视频（竖屏 9:16，30-45 秒）。

第一阶段重点：流程可解释、步骤可追踪、方案可对比。

## 技术路线

当前验证 6 类视频生成技术路线：

| 路线 | 说明 | 状态 |
|------|------|------|
| `local_frame_compose` | 本地图像帧合成 + FFmpeg | **Real (V0.2)** |
| `local_media_compose` | 本地素材合成（MoviePy/FFmpeg） | Mock |
| `template_programmatic_render` | Remotion 程序化模板渲染 | Mock |
| `ai_video_direct` | 大模型直接生成视频 | Reserved |
| `ai_asset_then_compose` | AI 素材 + 本地合成 | Mock |
| `hybrid_pipeline` | 混合编排流水线 | Mock |

> **V0.2 进展**：`local_frame_compose` 已支持真实 Pillow 帧生成 + FFmpeg MP4 合成。

## 测试用例

| ID | 名称 | 优先级 |
|----|------|--------|
| `case_ai_frontier_daily_001` | 今日 AI 前沿共享短视频 | 1 |
| `case_ai_news_short` | AI 资讯短视频 | 1 |
| `case_article_to_video` | 文章转视频 | 2 |
| `case_emotional_short` | 情绪短片 | 2 |
| `case_product_intro` | 产品介绍视频 | 1 |
| `case_image_motion` | 图片动起来 | 1 |
| `case_knowledge_explainer` | 知识讲解视频 | 1 |

## 页面路由

| 路径 | 说明 |
|------|------|
| `/video-lab` | 首页 |
| `/video-lab/test-cases` | 测试用例列表 |
| `/video-lab/methods` | 生成方案列表 |
| `/video-lab/experiments/new` | 创建实验 |
| `/video-lab/compare` | 结果对比 |
| `/video-lab/advice` | 总结建议 |

## 本地启动

### 依赖要求

- **Python 3.10+**
- **FFmpeg**（需在 PATH 中，或 `ffmpeg` 命令可用）
- **Pillow**（`requirements.txt` 中已包含）

### 后端

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:3000/video-lab`

## 测试命令

```bash
# 后端测试（全部）
python -m pytest tests/ -v

# 后端测试（核心）
python -m pytest tests/test_video_lab.py -v

# 本地渲染测试
python -m pytest tests/test_video_lab_local_frame.py -v

# Python 编译检查
python -m compileall app/ -q

# 前端 TypeScript 检查
cd frontend && npx tsc --noEmit
```

## 分支开发规范

```
main          ← 主分支，只接受合并，不直接开发
feature/*     ← 功能开发分支
```

- 所有功能开发从 `main` 切 `feature/*` 分支
- 不直接在 `main` 上开发
- 每轮任务完成后汇报 branch/base/status
- 提交前必须跑测试
- 不提交 .env / node_modules / dist / build / 真实视频大文件
- docs 和 README 随架构变化同步更新

## 当前限制

- 所有 adapter 均为 Mock 状态，不产出真实 MP4
- `ai_video_direct` 为 Reserved 状态，等待视频模型接入
- 实验结果暂存于内存/本地存储，非持久化数据库
- 后续接入真实能力时，只需实现对应 Adapter，不影响整体架构

## 下一阶段路线

```
V0.2：本地帧合成 + FFmpeg 输出真实 9:16 AI 资讯分享视频
V0.3：Remotion 模板渲染真实 MP4
V0.4：接入一个视频模型 Adapter
V0.5：LLM 拆脚本 + TTS + 图片生成 + 合成
V0.6：批量对比实验 + 产品化报告
```

## 文档

- [架构文档](docs/VIDEO_CAPABILITY_LAB_ARCHITECTURE.md)
- [技术路线矩阵](docs/VIDEO_METHODS_MATRIX.md)
- [开发流程](docs/DEVELOPMENT_WORKFLOW.md)
- [已知限制](docs/KNOWN_LIMITATIONS.md)
- [路线图](docs/VIDEO_CAPABILITY_LAB_ROADMAP.md)
- [变更日志](docs/CHANGELOG.md)
