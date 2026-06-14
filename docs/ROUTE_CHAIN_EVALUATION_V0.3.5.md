# V0.3 完整视频生成链路对比报告

> 测试日期：2026-06-14
> 测试输入：同一份 AI 前沿日报默认样例（3 条资讯）
> 测试目标：验证完整成片链路，以最终 MP4 为准

---

## 测试输入

```
今天有三条 AI 动态值得关注。

第一，OpenAI 发布新的推理模型能力，重点提升复杂任务分解和工具调用稳定性。

第二，Anthropic 更新 Claude Code 相关能力，进一步强化开发者在代码审查，重构和自动化任务中的使用体验。

第三，HeyGen 推出 HyperFrames 能力，可以通过 HTML 生成视频，为程序化视频制作提供了新的路线。

这三条信息共同说明，AI 视频和 AI Agent 正在从单点能力走向可组合的工作流。
```

---

## local_frame_tts_video

- **chainId**: local_frame_tts_video
- **画面来源**: Pillow 静态卡片帧
- **音频来源**: MiniMax TTS
- **字幕方式**: SRT（已烧入视频）
- **状态**: ✅ succeeded
- **是否生成最终视频**: ✅ 是
- **finalVideoUrl**: `/runtime/video_lab/experiments/chain_local_frame_tts_video_20ba9bcf/final_with_audio.mp4`
- **audioUrl**: `/runtime/video_lab/experiments/chain_local_frame_tts_video_20ba9bcf/audio/voiceover.mp3`
- **srtUrl**: `/runtime/video_lab/experiments/chain_local_frame_tts_video_20ba9bcf/subtitles/subtitles.srt`
- **hasVisual**: ✅ true
- **hasAudio**: ✅ true
- **hasReadableText**: ✅ true（字幕已烧入）
- **subtitleBurned**: ✅ true
- **audioDurationSec**: 17.24s
- **subtitleCount**: 3

### 优点
- 全自动，零人工介入
- 链路稳定，可复现
- SRT 字幕已成功烧入视频，字幕可读
- TTS 音频正常生成
- 无 API 报错

### 缺点
- 画面为静态信息卡片，缺乏动态表现力
- 节奏依赖语音时长，缺乏视觉变化
- 短视频感较弱，更像图文转视频

### 评分（1-5）

| 维度 | 评分 | 说明 |
|------|------|------|
| 信息准确性 | 4 | 文字精准传达 |
| 画面质量 | 2 | 静态卡片，信息密度低 |
| 声音自然度 | 4 | MiniMax TTS 较自然 |
| 字幕可读性 | 4 | 已烧入，清晰可见 |
| 节奏感 | 3 | 音频驱动，约17s，适合短视频 |
| 完整度 | 4 | 画面+音频+字幕齐全 |
| 自动化稳定性 | 5 | 全自动，链路稳定 |
| 成本可控性 | 5 | FFmpeg 本地，MimiMax TTS 成本低 |
| 产品化潜力 | 3 | 适合作为兜底链路，主线吸引力有限 |

**综合评分：3.8 / 5**

### 一句话结论

> 画面偏静态，但稳定、可控，适合作为兜底链路。视觉表现力不足，但作为纯文字转视频方案已可用。

---

## remotion_tts_video

- **chainId**: remotion_tts_video
- **画面来源**: Remotion React 模板
- **音频来源**: MiniMax TTS
- **字幕方式**: SRT（计划）
- **状态**: ❌ failed
- **是否生成最终视频**: ❌ 否
- **failedStep**: remotion_render
- **failedReason**: Remotion render succeeded but no video path found

### 失败分析

Remotion 渲染后 FFmpeg 合成阶段报错：

```
Error: FFmpeg quit with code 3752568763
ffmpeg version n7.1 ...
```

错误码 `3752568763` 疑似 FFmpeg 进程异常退出，可能是 Windows 环境兼容性问题。Remotion 内部调用 FFmpeg 时参数或路径处理有问题。

### 是否可修复

- 可修复：Remotion 的 FFmpeg 合成逻辑需要 Windows 兼容性修复
- 修复成本：中等（需调试 Remotion 渲染参数和 FFmpeg 路径）

### 评分（无法评分，链路未成功）

**一句话结论**

> Remotion 渲染环境存在 FFmpeg 兼容性问题，链路未跑通。需修复 Remotion 渲染环境后再评估。

---

## hyperframes_tts_video

- **chainId**: hyperframes_tts_video
- **状态**: ⚠️ manual_required
- **htmlUrl**: `/runtime/video_lab/experiments/chain_hyperframes_tts_video_fb9eea47/hyperframes/index.html`
- **finalVideoUrl**: （无，自动链路无法生成）
- **failedReason**: 需要人工将 HTML 放入 HeyGen HyperFrames 渲染后上传/指定 MP4

### 当前状态

HTML 已成功生成，人工渲染步骤**本轮未实际操作**。

因此本轮不参与最终视频质量评分，只记录为 `manual_required`。

### 一句话结论

> HyperFrames HTML 生成链路正常，但需人工 HeyGen 渲染，本轮未实际操作 MP4 生成。

---

## 横向评分表

| 链路 | 信息准确性 | 画面质量 | 声音自然度 | 字幕可读性 | 节奏感 | 完整度 | 自动化稳定性 | 成本可控性 | 产品化潜力 | 综合 |
|------|-----------|---------|-----------|-----------|--------|--------|-------------|-----------|-----------|------|
| local_frame_tts_video | 4 | 2 | 4 | 4 | 3 | 4 | 5 | 5 | 3 | **3.8** |
| remotion_tts_video | — | — | — | — | — | — | — | — | — | 链路失败 |
| hyperframes_tts_video | — | — | — | — | — | — | — | — | — | 人工未操作 |

---

## 最终路线判断

```
当前最佳完整视频链路: local_frame_tts_video
当前最佳画面链路:    local_frame_tts_video（目前唯一跑通全链路的）
当前兜底链路:        local_frame_tts_video（稳定兜底）
当前暂缓链路:        remotion_tts_video（修复 FFmpeg 兼容性问题后再测）
                    hyperframes_tts_video（需 HeyGen 人工操作，优先级低）

下一阶段是否继续深挖 Remotion: 是，但需先修复 FFmpeg 退出码问题
是否保留 local_frame 作为 fallback: 是，稳定可用
HyperFrames 是否值得继续人工验证: 可探索，但 HeyGen 插件限制多
TTS 是否值得保留为标准增强层: 是，已验证 MiniMax TTS + SRT 字幕链路可用
```

---

## 下一步建议

1. **优先**: 修复 `remotion_tts_video` 的 FFmpeg 退出码问题，Windows 环境兼容调试
2. **可选**: 人工实际操作一次 HeyGen HyperFrames，看 HTML 渲染效果上限
3. **探索**: local_frame 画面质量提升方向（如更多模板样式）
4. **暂缓**: AI 视频直出、AI 素材链路，等主链路评分完成后再接入
