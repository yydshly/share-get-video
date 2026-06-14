# TTS Subtitle Compose Route — V0.3.3

## 概述

V0.3.3 新增第四条真实技术路线：**tts_subtitle_compose**。

目标：验证 MiniMax TTS 旁白 + SRT 字幕是否能显著提升 AI 资讯共享视频的完播率和分享价值。

---

## 核心思路

```
同一份 AI 资讯内容
  → 生成口播稿
  → MiniMax TTS 生成音频
  → 生成 SRT 字幕文件
  → 生成静音画面（复用 local_frame_renderer）
  → FFmpeg 合成带声音/字幕的视频
  → 回填 Route Benchmark
  → 对比无声 vs 有声视频体验差异
```

---

## 路线状态

| 状态 | 值 |
|------|-----|
| `route_id` | `tts_subtitle_compose` |
| `status` | `real` |
| `engine` | `minimax-tts` |
| `resolution` | `1080x1920` (9:16 竖屏) |
| `API Required` | MiniMax TTS API Key |

### 依赖

**必须安装 `requests` 库**（V0.3.3.1 修复）：
```bash
pip install requests>=2.31.0
```
MiniMax TTS client 使用 `requests` 库调用 HTTP API。

### 字幕烧录 graceful fallback

如果 FFmpeg subtitles filter 在当前环境失败（例如 Windows 路径转义问题），路线会自动 fallback：

1. 尝试 `compose_av_with_subtitles`（视频 + 音频 + SRT 烧录）
2. 失败 → 尝试 `compose_video_with_audio`（视频 + 音频，仅音频合成）
3. 最终视频仍成功生成，SRT artifact 保留
4. manifest 记录 `subtitleBurned: false`, `subtitleFallback: true`

---

## 环境变量

```bash
# .env.example
MINIMAX_API_KEY=your_api_key_here
MINIMAX_GROUP_ID=
MINIMAX_TTS_MODEL=speech-2.8-hd
MINIMAX_TTS_VOICE_ID=male-qn-qingse
MINIMAX_TTS_SPEED=1.0
MINIMAX_TTS_VOLUME=1.0
MINIMAX_TTS_BASE_URL=https://api.minimaxi.com
```

---

## 技术实现

### 文件结构

```
app/video_lab/
  providers/minimax/
    __init__.py
    tts_client.py              # MiniMax TTS 客户端
  planners/
    voiceover_planner.py       # 口播稿生成器
    subtitle_planner.py        # SRT 字幕生成（扩展）
  renderers/
    ffmpeg_av_composer.py     # 音视频字幕合成器
  adapters/
    tts_subtitle_compose.py   # 9 步 adapter

tests/
  test_voiceover_planner.py   # 4 个测试
  test_subtitle_planner.py    # 6 个测试
  test_minimax_tts_client.py  # 8 个测试
  test_ffmpeg_av_composer.py  # 6 个测试
  test_tts_subtitle_route.py  # 5 个测试

docs/
  TTS_SUBTITLE_ROUTE_V0.3.3.md
```

### MiniMax TTS Client（providers/minimax/tts_client.py）

基于参考项目 `20260508_个人感悟生成情绪mv/services/audio_service.py` 实现。

**功能：**

- 读取环境变量 `MINIMAX_API_KEY` 等
- 调用 MiniMax TTS HTTP API (`/v1/t2a_v2`)
- 支持 voice_id / speed / volume / pitch 参数覆盖
- 重试机制（最多 2 次重试，针对特定错误码）
- 保存音频到 `runtime/video_lab/experiments/<experiment_id>/audio/voiceover.mp3`

**返回值：**

```python
{
    "success": bool,
    "audioPath": str,
    "audioUrl": str,
    "durationSec": float,
    "providerMessage": str,
}
```

### 口播稿生成器（planners/voiceover_planner.py）

**不调用 LLM**，基于模板生成：

- 从 lead 生成开场白
- 从 key points 生成要点口播句
- 生成固定结束语
- 分配每段时长（3-10 秒）

**返回值：**

```python
{
    "voiceoverText": "...",
    "segments": [
        {
            "index": 1,
            "text": "今天有三个AI信号值得关注...",
            "startSec": 0.0,
            "durationSec": 5.0
        }
    ],
    "estimatedDurationSec": 45
}
```

### SRT 字幕生成器（planners/subtitle_planner.py）

扩展现有 subtitle_planner，新增 `generate_srt_from_segments()`：

- 从 voiceover segments 生成 SRT 时间轴
- 每条字幕不超过 20 中文字符
- 写出 `.srt` 文件
- 保存到 `runtime/video_lab/experiments/<experiment_id>/subtitles/subtitles.srt`

### FFmpeg 音视频合成器（renderers/ffmpeg_av_composer.py）

**compose_av_with_subtitles()**：

```bash
ffmpeg -y \
  -i silent.mp4 \
  -i voiceover.mp3 \
  -vf "scale=...:...,subtitles='C:/path/to/subtitles.srt':force_style='Fontsize=18,...'" \
  -c:v libx264 -c:a aac -shortest \
  final_with_audio.mp4
```

### Adapter（tts_subtitle_compose.py）

**9 步流水线：**

1. **Receive Input** — 解析原始输入
2. **Structure Content** — 内容结构化
3. **Extract Key Points** — 提取关键点
4. **Generate Voiceover Plan** — 生成口播稿
5. **MiniMax TTS Generate Audio** — TTS 生成音频
6. **Generate SRT Subtitles** — 生成字幕文件
7. **Generate Silent Video** — 生成静音画面
8. **FFmpeg AV Composition** — 音视频字幕合成
9. **Generate Conclusion** — 写入 manifest

---

## 与其他路线的对比

| 维度 | local_frame_compose | template_programmatic_render | hyperframes_html_render | tts_subtitle_compose |
|------|---------------------|------------------------------|------------------------|----------------------|
| 状态 | real | real | manual | **real** |
| 声音 | ❌ 无 | ❌ 无 | ❌ 无 | ✅ **TTS 旁白** |
| 字幕 | 内嵌文字 | 内嵌文字 | ❌ | ✅ **SRT 烧录** |
| 自动化 | ✅ | ✅ | ❌（人工） | ✅ |
| API 依赖 | FFmpeg | Node.js | HeyGen | **MiniMax TTS** |

---

## 体验对比假设

无声视频（local_frame_compose）→ 有声有字幕视频（tts_subtitle_compose）：

预期提升：
- 完播率提升（观看门槛降低）
- 信息传达更生动
- 分享吸引力增强

待人工验证。

---

## 未来升级路径

1. **音频对齐**：使用 MiniMax TTS 返回的时间戳做字幕强制对齐
2. **多音轨**：添加背景音乐轨
3. **情感 TTS**：使用情感语音提升表现力
4. **字幕样式**：自定义字幕颜色/位置/动画

---

## 相关文档

- [ROUTE_BENCHMARK_V0.3.md](ROUTE_BENCHMARK_V0.3.md)
- [VIDEO_CAPABILITY_LAB_ROADMAP.md](VIDEO_CAPABILITY_LAB_ROADMAP.md)
- [CHANGELOG.md](CHANGELOG.md)
