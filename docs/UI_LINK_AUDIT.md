# UI 链路通断盘点与后期规划（截至 2026-06-15）

> 从 UI 入口视角，统计每个页面的"链路"是否端到端通到价值产出，并给出后期规划。
> 方法：扫描 `frontend/src/video-lab/pages/*.tsx` 的接口调用 → 对照 `app/video_lab/router.py` 已注册端点 → 判断端到端是否真正产出。
> 结论：没有"调用不存在端点"的断头链路；"未通"指的是**流程是否真正端到端交付价值**（很多页是死页/假数据/停半截/冗余）。

当前分支：`feature/v0.3.6-b1-shotplan-standardization`

## ✅ 已通（端到端产出价值）
| 页面 | 路由 | 后端链路 | 备注 |
|---|---|---|---|
| 🔎 技术探测台 | /video-lab/technique-probe | `/technique-probe` → 三路线各出整片→排名 | 本会话真跑验证 3/3 |
| 🎨 样式对比台 | /video-lab/style-sweep | `/style-sweep` → 一路线全部样式各出片 | 后端测试+UI验证；整片真跑待做 |
| 视频生成对比 | /video-lab/visual-compose | `/visual-compose` + `/visual-judge` | 出终片+视觉评分 |
| 调试台 | /video-lab/frame-preview | `/frame-preview`·`/clip-preview`·`/visual-judge` | 秒级单帧/片段预览 |
| 风格样片库 | /video-lab/style-gallery | `/style-samples*` 一整套 | 生成→评分→提模板→复用 |
| 评分趋势 | /video-lab/quality-history | `/quality-history`·`/quality-summary` | 只有分数曲线，无成片 |
| 老实验流 | /video-lab/experiments/* | `/experiments` → tts_subtitle_compose | 能出片，偏底层，被 visual-compose 取代 |

## 🟡 半通（能跑但停半截 / 很窄 / 旧）
| 页面 | 路由 | 问题 |
|---|---|---|
| 视频生成实验台(workbench v0.7.0) | /video-lab/workbench | **只调 `/clip-preview`，出不了终片**——最显眼却只到预览 |
| Remotion 表现范式 | /video-lab/remotion-style-family | `/style-family/compare` 写死仅 data_news vs card_stack 两个范式 |
| 多路线验证 | /video-lab/route-benchmark | 旧 `/route-benchmarks`，被技术探测台覆盖 |
| 链路测试台 | /video-lab/route-playground | 旧 `/chain-benchmarks`(chains)，被覆盖 |

## 🔴 未通（死页 / 假数据 / 硬编码）
| 页面 | 路由 | 问题 |
|---|---|---|
| 路线对比矩阵 | /video-lab/route-baseline-comparison | **零后端调用，纯静态文字**，假装在对比 |
| 结果对比 | /video-lab/compare | 用前端 seed 数据(SEED_TEST_CASES)，非实时 |
| 总结建议 | /video-lab/advice | 前端 `ADVISOR_RULES`(methodAdvice.ts) 硬编码假推荐 |
| 落地整体 | — | 推荐不是算出来的；后端 `advisor.py` 也硬编码（双重硬编码） |

## 📄 静态参考（合理，无需改）
首页 / 测试用例(test-cases) / 生成方案(methods)

## ♻️ 冗余
对比类共 5 页：route-benchmark / route-playground / route-baseline-comparison / compare / visual-compose —— 多数被新的技术探测台覆盖。
生成类：workbench / experiments-new / frame-preview 部分重叠。

## 🕳️ 宣传了但根本没有的链路
- **LLM 直生成视频**(Sora 类) / **混合编排**：methods、advisor 文案里提到，代码未实现（首页吹"8类技术路线"，实际只有 3 类渲染器：Pillow / Remotion / AI素材）。
- **data-driven 推荐**（落地）：不存在，advisor 硬编码。
- **产物画廊**：历史真实成片可重看/并排——现在只有 quality 分数曲线。

---

# 后期规划（按优先级）

## P0 — 打通断点，让显眼入口名副其实
1. **Workbench 接 `/visual-compose` 出终片**：现在最显眼的"实验台"只预览、出不了片，落差最大。
2. **落地闭环**：把 technique-probe 的综合分写回，**替掉 `advisor.py` + 前端 `ADVISOR_RULES` 硬编码**，让"总结建议"显示真实算出的推荐。
   - 前置约束见 [[technique-probe-feature]]：探测目前区分度不足（结构分饱和、视觉分 1-5 单帧分不开），落地前需确认探测能拉开差距。

## P1 — 清死页 / 收冗余（减少"看着有其实没用"）
3. 路线对比矩阵（死静态页）→ 删，或改成真调 `/technique-probe`。
4. 结果对比 / 总结建议（前端假数据）→ 接真实数据或下线。
5. 5 个对比页收敛成 1 条主线（留技术探测台为主）。

## P2 — 补能力
6. style-sweep 接视觉评分排名（此前选择"先只并排看"）。
7. **产物画廊**：历史真实成片可重看 / 并排（现在只有分数曲线）。
8. Remotion family：要么真实现 dashboard / subtitle_story，要么明确只留 2 种并改掉首页"8类"文案。

## P3 — 战略（大）
9. 探索 LLM 直生成视频路线（对齐目标① 多技术对比）。

---

## 已建成的两个核心单入口（本阶段成果）
- 🔎 技术探测台：跨技术对比（哪种**技术**最适合）
- 🎨 样式对比台：技术内样式对比（这技术下哪种**样式**最适合）
合起来覆盖核心三维：**质量 × 样式 × 技术路线**。相关约束见 [[technique-probe-feature]]，方向见 [[share-get-video-goal]]。
