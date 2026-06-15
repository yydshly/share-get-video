# 视频质量优化 · 待办交接文档

> 目的：把剩余的视频质量优化任务描述清楚，供另一个大模型/agent 冷启动接手。
> 场景：AI 资讯竖屏短视频（9:16，数字密集），要"信息准确 + 优雅 + 可对比"。

---

## 0. 当前架构速览（接手前必读）

### 链路（生成一支视频）
`app/video_lab/adapters/tts_subtitle_compose.py` 是主编排器，顺序：
1. `plan_shots()` 用 LLM 把报告规划成 shots（见下）
2. 构建 `key_points`（每条含 headline/display/narration/emphasisTerms/tone）
3. 生成口播稿 + MiniMax TTS 配音 + SRT/ASS 字幕（已按真实音频重缩放）
4. **可插拔视觉渲染器**产出静默视频
5. FFmpeg 合成 音频+字幕 → 成片
6. 自动结构层质量评分

样式/主题参数通过 `params` 字典一路透传到渲染器。

### 关键模块
| 模块 | 路径 | 作用 |
|------|------|------|
| LLM 内容规划 | `app/video_lab/planners/llm_content_planner.py` | `plan_shots()` → shots: {headline, display, narration, emphasisTerms[], tone} |
| 主题预设 | `app/video_lab/renderers/theme_presets.py` | tone→{accent,highlight,icon}；`resolve_shot_tone(kp)` |
| 可插拔视觉层 | `app/video_lab/renderers/visual/` | base/pillow/remotion/ai_asset/registry，每个产出静默视频 |
| Pillow 帧 | `app/video_lab/renderers/local_frame_renderer.py` → `frame_templates.py` | `generate_frames(... style_params=)` → `render_keypoint_template(...)` |
| Remotion | `remotion/src/AiNewsVideo.tsx` / `data.ts` / `renderers/remotion/props_builder.py` | React 模板，已有 tone 预设、CountUpNumber、DataBar、vstyle props |
| Providers | `app/video_lab/providers/minimax/` | `tts_client` / `chat_client`(多模态，支持图像理解) / `image_client`(文生图) |
| 质量评估 | `app/video_lab/quality/` | `video_quality.py`(结构层确定性) / `visual_judge.py`(感知层视觉模型,多帧) / `quality_log.py`(留痕趋势) |

### 调试与对比（已有）
- 调试台前端 `frontend/src/video-lab/pages/FramePreviewPage.tsx`：单帧/片段预览 + 全参数面板 + AI 评分
- 对比页 `VisualComposePage.tsx`：三路线并排 + 双层质量分 + 样式 JSON
- 趋势页 `QualityHistoryPage.tsx`
- 后端端点（`router.py`）：`/frame-preview` `/clip-preview` `/visual-compose` `/visual-judge` `/quality-history` `/quality-summary` `/visual-routes`

### 验证手段（重要）
- **Pillow 单帧预览**：`POST /video-lab/frame-preview`，~57ms 出图，不花 API，调样式首选
- **Remotion 片段**：`render_clip_preview(...)`，3-5s 片段 ~26s 渲完（整片要 150s+）
- 抽帧看图：`ffmpeg -y -i clip.mp4 -vf "select=eq(n\,95)" -vframes 1 out.png`
- 编译/类型检查：`python -m compileall app/ -q`；`cd remotion && npx tsc --noEmit`；`cd frontend && npx tsc --noEmit`
- 测试：`python -m pytest tests/ -q`
- ⚠️ Windows 终端是 GBK，中文会乱码（正常）；视频里中文正常

### 已完成（不要重做）
可插拔视觉层、LLM 内容规划(1:1 不丢条)、音画时序对齐、字幕分块(不截断)、结构层质量、视觉模型评委(多帧+一致性)、评分留痕趋势、调试台(单帧/片段/参数面板/AI评分)、三路线差异化动效(Pillow Ken Burns / Remotion 数字滚动+数据条 / AI素材背景)、样式旋钮(配色/对齐/图标/字号)、**主题自适应样式(tone→配色+图标，正面绿/负面琥珀/中性蓝)**。

---

## 1. 数据可视化（优先级 P0，最大专业感提升）

**目标**：把数字（39% / 57-77% / 0.84 / 千万）画成图，而不只是高亮文字。

**现状**：Remotion 已有 `findPrimaryStat()` + `CountUpNumber` + `DataBar`，但只处理**第一个百分比**；Pillow **完全没有图表**。

**做法**：
1. **数据结构化（推荐先做）**：在 `llm_content_planner.py` 的 plan schema 给每条 shot 增加 `metrics: [{label, value, unit}]`（如 `[{"label":"通过率","value":77,"unit":"%"}]`）。修改 `_SYSTEM_PROMPT`/`_build_user_prompt`/`_normalize_plan`。这样渲染由数据驱动，不用正则猜。adapter(`tts_subtitle_compose.py` 第 ~180 行 kps_list)与 `props_builder.py` 把 metrics 带下去。
2. **Remotion 扩展**（`AiNewsVideo.tsx`）：
   - 支持多指标（遍历 metrics，多条 DataBar/CountUp）
   - 区间值（57-77%）画成"区间带"（一条 bar 上标出 min-max 阴影段）
   - bar 颜色用该卡 tone 的 accent（已有 `accent` 变量）
3. **Pillow 加图表**（`frame_templates.py`）：新增 `draw_data_bar(draw, x, y, w, h, pct, color)` 和大号数字；在 `render_keypoint_template` 正文下方，当有主指标时画"大数字 + 进度条"。加参数 `show_data_viz: bool=True`，并在 `local_frame_renderer.generate_frames` 透传。

**验证**：Pillow 用单帧预览看 bar；Remotion 用片段。检查 bar 宽度=百分比、区间带位置正确。
**坑**：每卡最多 1-2 个主图，别堆满；中文字体已在 `text_layout.find_chinese_font`。

---

## 2. BGM + 音效（优先级 P1，最缺的"分享感"）

**目标**：加背景音乐 + 转场音效。现在成片**完全没有音乐**。

**做法**：
1. **素材**：放几首免版权 BGM 到 `app/video_lab/assets/audio/`（或试 MiniMax 是否有音乐生成 API；`image_client.py` 可参考写法）。
2. **混音**：在最终合成步（`app/video_lab/renderers/ffmpeg_av_composer.py` 的 `compose_av_with_subtitles`）把 BGM 用 FFmpeg `amix`/`volume` 压到旁白之下（约 -18dB ~ -22dB），循环到片长，首尾 fade。
3. **参数**：`params` 加 `bgm`(曲目名/none)、`bgmVolume`。透传：visual 不需要，BGM 在音频合成层，需把参数传到 av composer（adapter 第 8 步）。

**验证**：放出来听，确认不盖住人声。
**坑**：闪避(ducking，人声时自动压低 BGM)是进阶，先用固定低音量即可；注意 BGM 比人声短时要 loop（`-stream_loop -1` 或 aloop）。

---

## 3. Remotion 动效增强（优先级 P2，路线差异化）

**目标**：把 Remotion 的"动"做足（它的灵魂）。全在 `remotion/src/AiNewsVideo.tsx`。

**做法**：
- **卡间转场**：现在 Sequence 之间是硬切。给 KeyPointCard 加退场动画（最后 ~10 帧 opacity/translateX 渐出），或让相邻 Sequence 重叠做交叉淡入。
- **逐字标题**：headline 按字/词 stagger 入场（拆字符，每个延迟 opacity）。可做一个 `KineticText` 组件。
- **背景缓动**：加一个缓慢漂移的渐变/光斑 div（`interpolate(frame,...)` 驱动 position）。
- **强调词脉冲**：emphasis 词出现时 scale+glow 一下（在 `HighlightedText` 给高亮 span 加基于 frame 的 spring）。

**验证**：片段预览。**坑**：克制，别让动效喧宾夺主；改完 `npx tsc --noEmit`。

---

## 4. 零散修复 / 进阶（可选）

- **跨行高亮修复**：`frame_templates.py` `_draw_lines_with_highlights` 和 `AiNewsVideo.tsx` `getHighlightedSegments` 都是按行/整串匹配，当高亮词被换行拆开（如 "57-" / "77%"）就不高亮。修法：换行时保证 emphasis 词不被拆，或允许跨行匹配。
- **对比页可视化样式面板**：`VisualComposePage.tsx` 现在用样式 JSON，可做成按路线的取色器/下拉（参考 `FramePreviewPage.tsx` 的样式面板）。
- **字级音画同步**：MiniMax TTS `subtitle_enable=true` 可返回字级时间戳（`tts_client.py` 现在没用）。用它让字幕分块/强调词出现的时机精确对齐语音。
- **自动优化回路**：把"生成→视觉模型评分→按建议自动调参→再生成"做成一个循环，直到分数不再涨。评委返回 `suggestions`，可映射成 params 调整。

---

## 5. 推荐顺序

1. 数据可视化（P0，先做 metrics 结构化，再 Pillow + Remotion 渲染）
2. BGM + 音效（P1）
3. Remotion 动效增强（P2）
4. 零散修复按需

每做完一项：单帧/片段预览看效果 → 跑 `compileall` + `tsc` + 相关 `pytest` → 在调试台点「AI 视觉评分」看感知分有没有涨（趋势页留痕）。

---

## 6. 注意事项（沿用项目惯例）

- 不引入数据库/任务队列（留痕用 JSONL）
- 不破坏跑通的链路；新参数都做成**可选、默认保持现有行为**
- 不提交 runtime 产物、node_modules、真实大视频
- 改 `frame_templates.py` / `local_frame_renderer.py` / `AiNewsVideo.tsx` 时，新增参数用加法（带默认值），避免破坏现有渲染
- 中文文案里关键数字/机构名不能丢（信息准确是第一原则）
