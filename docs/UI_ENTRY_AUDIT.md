# Video Lab UI Entry Audit (V0.7.5)

> V0.7.5 重新审计首页列出的 16 个 UI 入口是否与实际实现一致。
>
> **方法**：基于 [docs/UI_LINK_AUDIT.md](UI_LINK_AUDIT.md) (V0.7.4 之前 d6505b6) 的成果，**重新读取每个页面的源码 + App.tsx 路由注册 + 后端 router.py 端点**，核对首页（[VideoLabHome.tsx](../frontend/src/video-lab/pages/VideoLabHome.tsx)）中的状态文案是否与实际行为一致。
>
> **本轮目的**：发现并修正首页状态文案的不准确之处；不修任何页面、任何后端、任何生成质量细节。
>
> **未做**：本环境无浏览器，未做真实的"打开页面 + 点击流程"端到端跑通；审计为**代码级静态审计**。

---

## 0. 当前策略

先打通 UI 入口与主流程；生成质量问题（Remotion 成片、音画不同步、样式差异）按 [OPEN_ISSUES_VIDEO_LAB.md](OPEN_ISSUES_VIDEO_LAB.md) 清单逐项排查。

本轮目标：

1. 确认首页所有入口可打开（路由存在 + 页面文件存在 + 后端端点可调）。
2. 确认首页状态文案与实际行为一致（不再误导用户）。
3. 记录坏入口、弱入口、静态入口、硬编码入口。
4. 同步刷新 [OPEN_ISSUES_VIDEO_LAB.md](OPEN_ISSUES_VIDEO_LAB.md) P1 区。

---

## 1. 审计结果总览

| 分组 | 页面 | 路径 | 路由 | 后端 | 真实数据 | 闭环 | 首页状态 | 实际 | 建议 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 主线 | 视频生成实验台 | `/video-lab/workbench` | ✅ | ✅ `/visual-compose` `/clip-preview` `/style-samples*` | Y | Y（保存样片+加入对比） | 主线入口 · 已通 | ✅ 已通 | 保持 |
| 主线 | 样片库 / 对比面板 | `/video-lab/style-gallery?tab=gallery&source=workbench` | ✅ | ✅ `/style-samples*` `/style-templates` `/style-gallery/*` | Y | Y（保存/对比/评分/升级模板） | 产物沉淀 · 已通 | ✅ 已通 | 保持 |
| 主线 | 样式对比台 | `/video-lab/style-sweep` | ✅ | ✅ `/style-sweep` | Y | N（仅看片） | 样式验证 · 已通但质量待排查 | ✅ UI 已通，质量问题见 P0 | 保持 |
| 验证 | 技术探测台 | `/video-lab/technique-probe` | ✅ | ✅ `/technique-probe` | Y | N（仅看排名） | 可用 | ✅ 已通 | 保持 |
| 验证 | 视频生成对比 | `/video-lab/visual-compose` | ✅ | ✅ `/visual-routes` `/visual-compose` `/visual-judge` | Y | Y（评分） | 可用 / 高级 | ✅ 已通 | 保持 |
| 验证 | 调试台 | `/video-lab/frame-preview` | ✅ | ✅ `/visual-routes` `/frame-preview` `/clip-preview` `/visual-judge` | Y | Y（评分） | 可用 | ✅ 已通 | 保持 |
| 验证 | 评分趋势 | `/video-lab/quality-history` | ✅ | ✅ `/quality-summary` `/quality-history` | Y | N（只读） | 可用 | ✅ 已通 | 保持 |
| 历史 | 创建实验 | `/video-lab/experiments/new` | ✅ | ✅ `/experiments` | Y | Y（localStorage） | 历史入口 | 🟡 仍功能，但被 visual-compose 取代 | 保持 / 后续可下线 |
| 历史 | 多路线验证 | `/video-lab/route-benchmark` | ✅ | ✅ `/routes` `/route-benchmarks` | Y | N | 历史入口 | 🟡 被技术探测台覆盖 | 保持 |
| 历史 | 链路测试台 | `/video-lab/route-playground` | ✅ | ✅ `/chain-benchmarks` | Y | Y（评分 + Markdown 导出） | 历史入口 | 🟡 被覆盖 | 保持 |
| **历史** | **路线对比矩阵** | `/video-lab/route-baseline-comparison` | ✅ | **❌ 零后端调用** | **N（纯硬编码文字）** | **N** | **历史入口** | **🔴 静态页（误导）** | **本轮已改为「静态页」** |
| 历史 | 结果对比 | `/video-lab/compare` | ✅ | ❌（读 localStorage） | N | N | 静态页 | 🔴 非实时数据 | 保持 |
| 历史 | 总结建议 | `/video-lab/advice` | ✅ | ❌ | N（ADVISOR_RULES 硬编码） | N | 待接真实数据 | 🔴 硬编码假推荐 | 保持 |
| 历史 | 生成方案 | `/video-lab/methods` | ✅ | ❌ | N（seed） | N（仅展示） | 参考页 | 📄 静态参考 | 保持 |
| 历史 | 测试用例 | `/video-lab/test-cases` | ✅ | ❌ | N（seed） | N（仅展示+跳 advice） | 参考页 | 📄 静态参考 | 保持 |
| 历史 | Remotion 表现范式 | `/video-lab/remotion-style-family` | ✅ | ✅ `/style-family/compare`（仅 2 范式） | 部分（仅预览对比） | N | 待清理 | 🟡 卡片/矩阵/路线图硬编码 | 保持 |

> **本轮发现并修正**：仅 `路线对比矩阵` 一处状态文案不准确，已在 V0.7.5 中从「历史入口」改为「静态页 · 纯硬编码」。
> 详见第 6 节。

---

## 2. 主流程入口（3 个）

### 2.1 视频生成实验台

- **路径**：`/video-lab/workbench`
- **是否可打开**：✅（路由 `App.tsx:42` 已注册）
- **主流程说明**：5 步流程的第 1-4 步都发生在 Workbench
- **真实数据 / 闭环**：
  - 预览 → `POST /clip-preview`
  - 完整视频 → `POST /visual-compose`（V0.7.2 接入）
  - 保存样片 → `POST /style-samples`（V0.7.2 接入）
  - 加入对比 → `POST /style-samples/{id}/compare`（V0.7.2 接入）
  - Workbench → Gallery 跳转：`/style-gallery?tab=gallery&source=workbench&sample_id=xxx`（V0.7.3 接入）
- **是否仍有断点**：⚠️ `ai_asset` 路线在 Workbench 标记为 `preview_only`（V0.7.x 已知限制）
- **结论**：✅ **端到端已通**（Pillow / Remotion 两条；AI 素材仍仅预览）
- **首页状态**：「主线入口 · 已通」→ ✅ 准确

### 2.2 样片库 / 对比面板

- **路径**：`/video-lab/style-gallery?tab=gallery&source=workbench`
- **是否可打开**：✅（路由 `App.tsx:39`）
- **主流程说明**：5 步流程的第 5 步
- **真实数据 / 闭环**：
  - 样片列表 → `GET /style-samples`
  - 视觉评分 → `POST /style-samples/{id}/judge`
  - 加入/移出对比 → `POST /style-samples/{id}/compare` `POST /style-samples/{id}/status`
  - 升级模板 → `POST /style-samples/{id}/promote-template`
  - V0.7.3 增强：Workbench 样片识别（`isWorkbenchSample`）+ 来源筛选 + URL 定位高亮
- **结论**：✅ **端到端已通**
- **首页状态**：「产物沉淀 · 已通」→ ✅ 准确

### 2.3 样式对比台

- **路径**：`/video-lab/style-sweep`
- **是否可打开**：✅（路由 `App.tsx:44`）
- **真实数据**：✅ `POST /style-sweep` 真跑
- **闭环**：N（并排看片，无保存 / 评分 / 模板升级）
- **质量问题（不修）**：用户实测发现 Remotion 样式差异偏小、缺图、音画不对应
- **结论**：✅ **UI 已通**（质量待排查）
- **首页状态**：「样式验证 · 已通但质量待排查」→ ✅ 准确

---

## 3. 验证工具入口（4 个）

### 3.1 技术探测台

- **路径**：`/video-lab/technique-probe`
- **是否可打开**：✅（`App.tsx:43`）
- **真实数据**：✅ `POST /technique-probe`（三路线各出整片+综合分）
- **闭环**：N（看排名，不保存）
- **首页状态**：「可用」→ ✅ 准确（是「可用」级，没把它放主流程）
- **附加说明**：本会话已真跑过 3/3（见 [UI_LINK_AUDIT.md](UI_LINK_AUDIT.md) §✅ 已通）

### 3.2 视频生成对比

- **路径**：`/video-lab/visual-compose`
- **是否可打开**：✅（`App.tsx:36`）
- **真实数据**：✅ `POST /visual-compose` `POST /visual-judge`
- **闭环**：Y（视觉评分）
- **首页状态**：「可用 / 高级」→ ✅ 准确

### 3.3 调试台

- **路径**：`/video-lab/frame-preview`
- **是否可打开**：✅（`App.tsx:37`）
- **真实数据**：✅ `POST /frame-preview` `POST /clip-preview` `POST /visual-judge`
- **闭环**：Y（视觉评分）
- **首页状态**：「可用」→ ✅ 准确

### 3.4 评分趋势

- **路径**：`/video-lab/quality-history`
- **是否可打开**：✅（`App.tsx:38`）
- **真实数据**：✅ `GET /quality-summary` `GET /quality-history`
- **闭环**：N（只读）
- **首页状态**：「可用」→ ✅ 准确

---

## 4. 历史 / 待清理入口（9 个）

### 4.1 创建实验

- **路径**：`/video-lab/experiments/new`
- **是否可打开**：✅
- **真实数据**：✅ `POST /experiments` + localStorage
- **闭环**：Y（localStorage 保存 + 跳转详情/对比）
- **状态**：「历史入口」
- **结论**：仍功能（V0.4.x 时代的实验流），但被 [visual-compose](#32-视频生成对比) 取代
- **建议**：保持；后续可下线

### 4.2 多路线验证

- **路径**：`/video-lab/route-benchmark`
- **是否可打开**：✅
- **真实数据**：✅ `GET /routes` `POST /route-benchmarks`
- **状态**：「历史入口」
- **结论**：被 [技术探测台](#31-技术探测台) 完全覆盖
- **建议**：保持

### 4.3 链路测试台

- **路径**：`/video-lab/route-playground`
- **是否可打开**：✅
- **真实数据**：✅ `POST /chain-benchmarks`
- **闭环**：Y（评分 + Markdown 导出）
- **状态**：「历史入口」
- **结论**：被 [技术探测台](#31-技术探测台) 覆盖
- **建议**：保持

### 4.4 路线对比矩阵（**本轮修正**）

- **路径**：`/video-lab/route-baseline-comparison`
- **是否可打开**：✅（路由存在）
- **真实数据**：❌ **零后端调用**，纯前端硬编码的 Pillow / Remotion / AI 素材 baseline 文字 + 旧文档链接
- **闭环**：N
- **首页状态**：「历史入口」→ **本轮改为「静态页」**（更准确：与 `4.5 结果对比` 一档）
- **旧审计**：[UI_LINK_AUDIT.md](UI_LINK_AUDIT.md) 🔴 路线对比矩阵 — **零后端调用，纯静态文字**
- **建议**：要么删，要么改成真调 `/technique-probe`（旧审计 P1-3）

### 4.5 结果对比

- **路径**：`/video-lab/compare`
- **是否可打开**：✅
- **真实数据**：❌（读 `localStorage`，非实时后端）
- **状态**：「静态页」→ ✅ 准确
- **结论**：用户实测看到的对比数据是旧 localStorage 留痕；不能反映最新后端状态
- **建议**：要么改读 `/experiments/{id}`，要么下线

### 4.6 总结建议

- **路径**：`/video-lab/advice`
- **是否可打开**：✅
- **真实数据**：❌（纯 seedData + `ADVISOR_RULES` 硬编码假推荐）
- **状态**：「待接真实数据」→ ✅ 准确
- **旧审计**：[UI_LINK_AUDIT.md](UI_LINK_AUDIT.md) 🔴 **前端 ADVISOR_RULES(methodAdvice.ts) 硬编码假推荐**；后端 `advisor.py` 也硬编码（**双重硬编码**）
- **建议**：接 technique-probe 真实推荐（受 [[technique-probe-feature]] 区分度约束）

### 4.7 生成方案

- **路径**：`/video-lab/methods`
- **是否可打开**：✅
- **真实数据**：N（seedData）
- **状态**：「参考页」→ ✅ 准确
- **附加说明**：文案里提到「6 类视频生成方案」，实际渲染器只有 3 类（Pillow / Remotion / AI 素材）。文案与实现不符，但页面是静态说明页，影响有限

### 4.8 测试用例

- **路径**：`/video-lab/test-cases`
- **是否可打开**：✅
- **真实数据**：N（seedData）
- **状态**：「参考页」→ ✅ 准确

### 4.9 Remotion 表现范式

- **路径**：`/video-lab/remotion-style-family`
- **是否可打开**：✅
- **真实数据**：部分（仅 `POST /style-family/compare`，且只支持 `data_news` / `card_stack` 两范式）
- **状态**：「待清理」→ ✅ 准确
- **结论**：卡片/矩阵/路线图全硬编码，仅对比预览真；与新 [主流程 - Workbench](#21-视频生成实验台) 重复
- **建议**：保留 2 范式对比即可；其余硬编码部分考虑删除

---

## 5. 宣传了但根本没有的链路（沿用旧审计 §🕳️）

> 来自 [UI_LINK_AUDIT.md](UI_LINK_AUDIT.md) §🕳️；V0.7.5 重新核对后**仍成立**：

- **「LLM 直生成视频」(Sora 类)** / **「混合编排」** — 在 [VideoMethodsPage](../frontend/src/video-lab/pages/VideoMethodsPage.tsx) `VideoMethodsPage.tsx` 和 [VideoAdvicePage](../frontend/src/video-lab/pages/VideoAdvicePage.tsx) `VideoAdvicePage.tsx` 的文案里提到，**代码未实现**。
  - 实际渲染器只有 3 类：`local_frame_compose`（Pillow）/ `template_programmatic_render`（Remotion）/ `ai_asset_then_compose`（AI 素材）。
- **「data-driven 推荐」（落地）** — 不存在；advisor 双重硬编码。
- **「产物画廊」** — 已在 V0.7.3 用 Style Gallery 解决（Workbench 样片识别 + 来源筛选）；但「历史真实成片可重看 / 并排」这一形态仍未实现（仅 quality 分数曲线）。

---

## 6. 本轮修正（V0.7.5）

### 6.1 修正首页状态文案

**文件**：[frontend/src/video-lab/pages/VideoLabHome.tsx](../frontend/src/video-lab/pages/VideoLabHome.tsx)
**位置**：`HISTORY_ENTRIES[3]`（路线对比矩阵）
**变更**：

| 字段 | 旧 | 新 |
| --- | --- | --- |
| `status` | `"历史入口"` | `"静态页"` |
| `statusColor` | `"#64748b"` | `"#64748b"`（不变） |
| `statusBg` | `"#f1f5f9"` | `"#f1f5f9"`（不变） |
| `desc` | "Pillow / Remotion / AI 素材 三路线 baseline 对比。" | "Pillow / Remotion / AI 素材 三路线 baseline 对比（**纯硬编码静态页，零后端调用**）。" |

**理由**：旧审计 [UI_LINK_AUDIT.md](UI_LINK_AUDIT.md) §🔴 已明确标"零后端调用，纯静态文字，假装在对比"。「历史入口」语义偏轻（暗示过去是功能），「静态页」更准确。

### 6.2 不修正的部分

- 视频生成实验台：原审计标「🟡 半通（只预览）」；V0.7.2 已接 `/visual-compose` 全片，V0.7.2+ 真实闭环。**首页状态仍写「主线入口 · 已通」** → 准确
- 样片库：V0.7.3 已加 Workbench 样片识别；**首页状态「产物沉淀 · 已通」** → 准确
- 样式对比台：质量问题（Remotion 缺图/音画不对应）是 P0 已知；**首页状态「样式验证 · 已通但质量待排查」** → 准确

---

## 7. 需要后续处理的问题

> 本节作为 [OPEN_ISSUES_VIDEO_LAB.md](OPEN_ISSUES_VIDEO_LAB.md) P1 区的补充。**本轮不修**。

### P0（仅记录，不在本轮修复）

- V0.7.5 巡检后**没有新发现** P0 问题；已知的成片质量问题见 [OPEN_ISSUES_VIDEO_LAB.md](OPEN_ISSUES_VIDEO_LAB.md) P0 区。

### P1（UI 入口相关）

1. **首页「路线对比矩阵」状态文案误导**（V0.7.5 已修正为「静态页」）。
2. **「5 个对比页」冗余**（route-benchmark / route-playground / route-baseline-comparison / compare / visual-compose）：多数被技术探测台覆盖。
3. **首页「VideoMethodsPage 文案提到 6 类技术，代码只有 3 类」**：用户从生成方案页可能误以为有 LLM 直出视频 / 混合编排能力。
4. **结果对比页（`/video-lab/compare`）读 localStorage 非实时**：用户看到的对比可能是过时的。

### P2（能力相关）

- 「LLM 直生成视频」/「混合编排」在文案里宣传但代码未实现。
- 「产物画廊 — 历史真实成片可重看 / 并排」未实现（quality 分数曲线代替之）。
- Remotion 表现范式页的硬编码部分需清理。

---

## 8. 与首页 / OPEN_ISSUES 的对应关系

| 文档 | 关系 |
| --- | --- |
| [VideoLabHome.tsx](../frontend/src/video-lab/pages/VideoLabHome.tsx) | 16 个入口的状态文案来源 |
| [docs/UI_LINK_AUDIT.md](UI_LINK_AUDIT.md) | V0.7.4 之前的旧审计（方法学 + 早期结论） |
| [docs/UI_ENTRY_AUDIT.md](UI_ENTRY_AUDIT.md) | **本文件** — V0.7.5 重新审计 + 本轮修正 |
| [docs/OPEN_ISSUES_VIDEO_LAB.md](OPEN_ISSUES_VIDEO_LAB.md) | 已知问题清单；本轮新增的 P1 项已同步进去 |

---

*审计人：V0.7.5 流程总控台巡检*
*方法：源码级静态审计（非浏览器实跑）；基于 V0.7.4 d6505b6 旧审计迭代*
*环境：Windows 11 + bash（git）+ Node.js（typecheck）*
