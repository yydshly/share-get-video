# 开放问题记录 — Video Lab

> 记录当前分支上已知但暂不阻塞主线的问题。会在后续阶段逐步处理。

---

## 1. Card Stack prev/next 图层可见性（已修复 V0.6.5.2）

**问题**：V0.6.5.1 报告中，抽帧无法确认 prev/next 图层是否可见。

**状态**：✅ 已修复（V0.6.5.2）— 通过增大 offset（prev: 140→220, next: -120→-220）、提高 opacity（prev: 0.65→0.75, next: 0.40→0.60）、添加蓝色/青色边框和 PREV/NEXT 角标，使两层在抽帧中清晰可见。

**遗留**：验证期标识（PREV/NEXT 角标）后续需替换为更自然的视觉语言。

---

## 2. V0.6.5.1 本地 local diff 必须清理

**问题**：V0.6.5.1 报告发现工作区存在削弱 V0.6.5 效果的 local diff（offsetX 140→120，-120→-100，移除 zIndex）。

**状态**：✅ 已处理 — V0.6.5.2 开始时执行 `git checkout -- remotion/src/AiNewsVideo.tsx` 丢弃。

---

## 3. V0.6.5.1 文档测试结果写"待执行"

**问题**：V0.6.5.1 文档中 pytest 测试标注"待执行"但实际无 test 文件。

**状态**：✅ 确认无 test 文件，非问题。

---

## 4. /style-family/compare 是连续生成而非并行生成

**问题**：`/style-family/compare` 在后端连续调用 `render_clip_preview`（先 Data News 再 Card Stack），不是真正的并行。

**状态**：⚠️ 已知限制，暂不影响功能。如后续需要真正并行，可考虑 asyncio.gather。

---

## 5. Card Stack 是否值得继续投入

**问题**：Card Stack 短视频信息流感是否真的优于 Data News，需等待主线工作台用户反馈后再决定。

**状态**：⏳ 待定 — V0.7.0 工作台已上线，可通过用户人工确认收集反馈。

---

## 6. AI 素材路线完整预览未接入

**问题**：`/clip-preview` 对 `ai_asset_then_compose` 支持 Ken Burns 片段，但 AI 背景图生成较慢（30秒+），当前 UI 标记为"暂未接入预览"。

**状态**：⚠️ 已知限制，AI 素材路线在 V0.7.0 中标记为 `preview_only`。

---

## 7. Remotion 路线未做 LLM 内容规划

**问题**：当前 `render_clip_preview` 对 Remotion 路线使用 `plan_shots` 做简单 content structuring，但未调用 LLM 做深入内容规划（如从报告提取 metrics、emphasisTerms 等）。

**状态**：⏳ 后续如需提升 Remotion 视频内容质量，可增强 `plan_shots` 的 LLM 调用。

---

## 8. 完整视频生成未接入工作台

**问题**：V0.7.0 工作台"生成完整视频"按钮为占位，下一阶段才接入。

**状态**：⏳ 计划在下一阶段接入 TTS + 字幕合成链路。

---

*最后更新：V0.7.0主线*
