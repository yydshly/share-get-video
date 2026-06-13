# Video Methods Matrix

## 概览

| Category | 名称 | 成本 | 可控性 | 稳定性 | 产品化 |
|----------|------|------|--------|--------|--------|
| `local_frame_compose` | 本地图像帧合成 | 低 | 高 | 高 | 高 |
| `local_media_compose` | 本地媒体素材合成 | 低 | 高 | 高 | 高 |
| `template_programmatic_render` | Remotion 程序化模板 | 中 | 高 | 中 | 高 |
| `ai_video_direct` | 大模型直接生成 | 极高 | 低 | 低 | 中 |
| `ai_asset_then_compose` | AI 素材+本地合成 | 高 | 中 | 中 | 中 |
| `hybrid_pipeline` | 混合编排流水线 | 高 | 中 | 中 | 高 |

---

## 1. local_frame_compose - 本地图像帧合成

### 描述
使用 Pillow / Canvas / OpenCV 生成图像帧，再用 FFmpeg 合成视频。适合程序化生成固定模板内容。

### 适合场景
- 固定模板视频批量生成
- 数据可视化动画
- 文字动态效果（缩放、平移、淡入淡出）
- 简单图标动画

### 不适合场景
- 复杂真实场景渲染
- 高逼真度人物/风景
- 需要创意运动的场景

### 输入要求
图片素材 + 动画参数（位移、缩放、旋转、淡入淡出）

### 输出形式
MP4 / WebM

### 后续真实接入
```python
# adapters/local_frame_compose.py
from PIL import Image, ImageDraw, ImageFont
import subprocess

def run_local_frame_compose(...):
    # 生成帧序列
    frames = generate_frames(input_payload, params)
    # 调用 FFmpeg 合成
    video_path = ffmpeg_concat(frames, output_path)
    return VideoExperimentResult(videoUrl=video_path, ...)
```

---

## 2. local_media_compose - 本地媒体素材合成

### 描述
使用 MoviePy / FFmpeg 对图片、音频、字幕、BGM、已有视频片段做合成。适合素材拼接和后期编排。

### 适合场景
- 多素材组合编排
- 音频+画面同步
- 字幕压制（SRT → burn-in）
- BGM 适配和混音

### 不适合场景
- 从零生成视觉内容
- 复杂转场效果（超过 FFmpeg 内置能力）
- AI 生成素材整合（需要 AI 模型介入）

### 输入要求
视频片段 / 图片 / 音频 / 字幕 SRT

### 输出形式
MP4 / WebM

### 后续真实接入
```python
# adapters/local_media_compose.py
from moviepy.editor import (
    ImageClip, AudioFileClip, concatenate_videoclips,
    TextClip, CompositeVideoClip
)
```

---

## 3. template_programmatic_render - Remotion 程序化模板渲染

### 描述
用 React / CSS / SVG / Canvas 做模板化视频渲染，适合资讯、日报、产品介绍、知识卡片等结构化内容。

### 适合场景
- 资讯/日报视频（结构化信息展示）
- 产品介绍（品牌调性一致）
- 知识卡片（图表+文字）
- 数据报告视频
- 结构化图文视频

### 不适合场景
- 高逼真度人物场景
- 自由创意内容
- 实时渲染性能要求高（单视频渲染 5-30 分钟）

### 输入要求
模板参数 JSON + 数据源

### 输出形式
MP4 / WebM

### 后续真实接入
```python
# adapters/remotion_template.py
import subprocess

def run_remotion_template(...):
    # 1. 将参数写入 JSON
    write_template_input(input_payload, params)
    # 2. 调用 Remotion CLI
    result = subprocess.run(
        ["npx", "remotion", "render", "InsightCardVideo", "--output=/tmp/video.mp4"],
        capture_output=True
    )
    # 3. 返回视频路径
    return VideoExperimentResult(videoUrl="/tmp/video.mp4", ...)
```

---

## 4. ai_video_direct - 大模型直接生成视频

### 描述
使用文生视频 / 图生视频 / 首尾帧视频 / 主体参考视频等模型直接生成内容。

### 适合场景
- 情绪/氛围短片（强视觉冲击）
- 图片动态化（图生视频）
- 创意内容探索（快速原型验证）
- 背景素材生成

### 不适合场景
- 需要精确文字/字幕（AI 生成视频字幕不可控）
- 结构化信息承载（资讯、日报、产品介绍）
- 批量一致性要求高
- 成本敏感型批量生产

### 输入要求
文本 prompt / 参考图片 / 首尾帧

### 输出形式
MP4 / WebM

### 状态
Reserved / not_configured - 等待视频模型 API 接入

### 后续真实接入
```python
# adapters/ai_video_direct.py
import openai  # or kling, runway, etc.

def run_ai_video_direct(...):
    response = openai.Video.create(
        model="sora-1",
        prompt=input_payload["prompt"],
        ...
    )
    return VideoExperimentResult(videoUrl=response.url, ...)
```

---

## 5. ai_asset_then_compose - AI 素材 + 本地合成

### 描述
LLM 生成脚本、旁白、字幕、图片提示词，TTS 生成语音，图像模型生成图片，最后由 Remotion / FFmpeg 合成。

### 适合场景
- 长视频内容制作（>2 分钟）
- 多模态内容整合（文字+图片+音频+视频）
- 半自动化视频流水线
- 内容+视觉双重质量要求

### 不适合场景
- 实时性要求高（多阶段串行，总耗时 10-30 分钟）
- 成本敏感型项目
- 需要精确逐帧控制（LLM 生成内容有随机性）

### 输入要求
文本内容 / 素材描述 / 旁白脚本

### 输出形式
MP4 / WebM

### 后续真实接入
```python
# adapters/ai_asset_then_compose.py
# Stage 1: LLM 拆脚本
script = openai.ChatCompletion.create(
    messages=[{"role": "user", "content": f"拆分视频脚本: {input_payload['content']}"}]
)
# Stage 2: TTS
audio = elevenlabs.TTS(text=script)
# Stage 3: 图像生成
images = [dalle.generate(p) for p in script.image_prompts]
# Stage 4: 合成
video = remotion.compose(images, audio, ...)
```

---

## 6. hybrid_pipeline - 混合编排流水线

### 描述
按场景自动选择：本地合成、Remotion、AI 视频、AI 图片、TTS、FFmpeg 等能力组合。

### 适合场景
- 复杂多模态内容
- 需要多技术配合
- 按需调度最优路径
- 产品化批量生产

### 不适合场景
- 简单单一步骤（用混合编排是杀鸡用牛刀）
- 实时渲染要求
- 高度定制化单作品

### 输入要求
场景描述 + 多模态输入

### 输出形式
MP4 / WebM（多格式版本）

---

## AI 资讯共享视频方案选择规则

### 推荐：template_programmatic_render

**原因**：AI 资讯共享视频要求信息准确、结构清晰、字幕可控、旁白稳定、批量生成能力强。

- Remotion 模板化渲染确保文字准确
- 批量生成一致性高
- 字幕与旁白时间轴精确对齐
- 产品化成本低

### 备选：ai_asset_then_compose / local_media_compose

- `ai_asset_then_compose`：适合后续增强版，加入 AI 生成封面、背景素材
- `local_media_compose`：适合素材已准备好的情况，低成本快速产出

### 不推荐：ai_video_direct

**原因**：大模型直接文生视频不适合承载精确信息表达。

- 字幕不可控，可能错漏
- 信息准确性风险高
- 批量一致性差
- 成本极高
- 更适合作为背景素材或情绪镜头，不适合作为主要内容
