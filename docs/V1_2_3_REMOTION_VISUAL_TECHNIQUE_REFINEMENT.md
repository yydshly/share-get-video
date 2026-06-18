# V1.2.3 Remotion Visual Technique Refinement

## 1. 背景

V1.2.5+ 已实现 5 个 `visualTechnique` 并接入 Visual Technique Matrix：

```text
academic_sketch
blueprint
data_viz_dashboard
agent_sandbox_25d
kinetic_code_typography
```

UI 验收阶段用户已看到 5 个样片能生成。问题从"能不能生成"升级为"视觉效果是否清晰、可辨识、可验收"。

本次任务**只做 5 个现有 visualTechnique 的视觉精修**，不新增 technique，不改后端，不改 UI 验收逻辑。

## 2. 本次精修要点

### 2.1 academic_sketch — 学术手绘草稿流

| 维度 | 之前 | 之后 |
|---|---|---|
| paperBg | `#faf7f2`（偏白） | `#f1eadc`（暖米色，去过曝） |
| 网格线 opacity | `0.18` | `0.32`（minor）/ `0.20`（major） |
| 网格层 | 1 层 | 2 层（minor 32px + major 160px） |
| 边距线 | `1px` 红色 `0.28` opacity | `1.5px` 红色 `0.45` opacity |
| 纸张颗粒 | `0.04` opacity | `0.06` opacity |
| 中央软光带 | 无 | 新增 `rgba(255,250,240,0.55)` radial（增加 paper 感） |
| 边缘 vignette | `0.15` | `0.22` |

AcademicSketchLayer 同步增强：

| 元素 | 之前 | 之后 |
|---|---|---|
| underline 笔画粗细 | `2.5` / `2` | `3.5` / `2.8` |
| underline opacity | `0.35` / `0.25` | `0.55` / `0.45` |
| circle stroke | `2` 宽度 / `0.4` opacity | `2.8` 宽度 / `0.6` opacity |
| circle 尺寸 | 58×52 | 68×60 |
| 箭头 stroke | `2` 宽度 / `0.3` opacity | `3` 宽度 / `0.5` opacity |
| 问号字号 | 48 / 40 | 58 / 50 |
| 问号 opacity | 0.22 / 0.18 | 0.42 / 0.38 |
| 星号字号 | 36 / `0.2` opacity | 46 / `0.4` opacity |

### 2.2 blueprint — 工程蓝图晒图风

| 维度 | 之前 | 之后 |
|---|---|---|
| lineMinor opacity | `0.16` | `0.24` |
| lineMajor opacity | `0.36` | `0.55` |
| ink opacity | `0.75` | `0.85` |
| corner ticks 边长 | 30px | 36px |
| corner ticks 笔画 | `2px` | `2.5px` |
| 技术标签 | 无 | 4 个：`SYS-01 · BLUEPRINT v0.3` / `FLOW · A→B` / `NODE · 01 / 04` / `SCALE 1:1 · UNIT mm` |
| Coordinate ruler ticks | 无 | 顶部 16 个、左侧 6 个（细小刻度） |

### 2.3 data_viz_dashboard — 数据动态看板

| 维度 | 之前 | 之后 |
|---|---|---|
| accentCyan / Purple | `0.85` / `0.78` opacity | `0.95` / `0.90` opacity |
| 柱状图数量 | 8 根 | 10 根 |
| 柱状图尺寸 | 32% × 26% | 38% × 30% |
| 柱状图 opacity | `0.85` | `0.95` |
| 折线图尺寸 | 44% × 28% | 50% × 30% |
| 折线图 stroke | `1.5` | `2` |
| 折线点 radius | `1.4` | `1.6` |
| 圆环图尺寸 | 26% × 32% | 30% × 36% |
| 圆环图 stroke | `6` | `6`（加 glow drop-shadow） |
| Panel border | `0.30-0.35` opacity | `0.45-0.50` opacity |
| Panel box-shadow | 无 | `0 0 18px rgba(80,180,230,0.10)` |
| Dashboard header | 无 | 新增 `METRICS · BENCHMARK v0.3 · ● LIVE` 顶部条 |
| Metric chips | `0.65rem` / `0.5rem` padding | `0.78rem` 粗体 / `0.65rem` padding |
| Metric chips 边框 | `1px` | `1.5px` |
| Metric chips 阴影 | `0.25 opacity` glow | `0.4 opacity` glow |

### 2.4 agent_sandbox_25d — 智能体沙盒模拟

| 维度 | 之前 | 之后 |
|---|---|---|
| node 尺寸 | 64 / 56 / 52 / 50 / 46 | 88 / 80 / 72 / 70 / 64 |
| node 边框 | `1.5px` | `2px` |
| node 阴影 | `0.5 opacity` | `0.67 opacity` (0xaa) |
| node 中心圆 | 8px | 10px + 强 glow |
| node 标签字号 | `0.55rem` | `0.78rem` 粗体 |
| 连接线 stroke | `0.25` / `0.30 opacity` | `0.5` / `0.55 opacity` + drop-shadow |
| 连接线阈值 | 38 | 42（更多连接） |
| 数据包尺寸 | 6px | 10px |
| 数据包阴影 | 10px + 18px | 14px + 26px |
| Sandbox platform panel | 无 | 新增底部 `SANDBOX PLATFORM · v0.3` 紫色 platform |
| Tag 标签 | v0.1 / `0.6rem` | v0.3 / `0.68rem` 粗体 |

### 2.5 kinetic_code_typography — 动态代码排版

| 维度 | 之前 | 之后 |
|---|---|---|
| editor panel 尺寸 | 50% × 70% | 58% × 78% |
| editor panel 边框 | `1px` / `0.30 opacity` | `1.5px` / `0.45 opacity` |
| editor 阴影 | `0.12 opacity` | `0.18 opacity` |
| 圆点尺寸 | 8px | 10px |
| 文件名 | `0.6rem` 普通 | `0.7rem` 粗体 + `● TS` tag |
| 代码行 font-size | `0.62rem` | `0.78rem` |
| 代码行 line-height | `1.4` | `1.5` |
| 代码行行号区 | 18px / 0.6 opacity | 22px / 0.7 opacity |
| 普通文字色 | `#c9d1d9` | `#e6edf3`（更亮） |
| 关键字/函数 weight | 默认 | `600` |
| Cursor 尺寸 | 6×11 | 7×14 |
| terminal panel 尺寸 | 40% × 32% | 44% × 36% |
| terminal 标题 | `▶ terminal` `0.6rem` | `▶ TERMINAL · zsh` `0.65rem` 粗体 |
| terminal log font-size | `0.58rem` | `0.72rem` |
| terminal log weight | `0.9 opacity` | `500` |
| terminal 背景 | `0.78 opacity` | `0.86 opacity` |
| 顶部 label | v0.1 / `0.6rem` | v0.3 / `0.68rem` 粗体 |

## 3. 改动文件清单

| 文件 | 改动 |
|---|---|
| `remotion/src/AiNewsVideo.tsx` | 5 个 visualTechnique BackgroundLayer 分支精修；AcademicSketchLayer 同步增强 |
| `docs/V1_2_3_REMOTION_VISUAL_TECHNIQUE_REFINEMENT.md` | 新增（本文档） |

## 4. 显式不做

- 不新增第 6 个 visualTechnique
- 不改 Style Sweep / Style Gallery / Recipe System
- 不改后端接口 / props_builder 白名单 / VALID_VISUAL_TECHNIQUES
- 不改 UI 验收状态逻辑（VisualTechniqueVariantMatrix）
- 不引入新依赖
- 不把任何 technique 标记为 `visually_accepted`

## 5. 验收方式

用户在 `http://localhost:3002/video-lab/remotion-style-family` 点击"运行视觉技法矩阵"，
应观察到：

1. **academic_sketch**：纸张变暖黄，网格和手绘批注明显（不再过曝）
2. **blueprint**：更像工程蓝图，可见技术标签、坐标刻度
3. **data_viz_dashboard**：更像数据看板，图表更大更亮，顶部有 `METRICS · BENCHMARK` 标签
4. **agent_sandbox_25d**：节点和标签更大更清楚，底部有 platform 标签，数据包更亮
5. **kinetic_code_typography**：编辑器区域更大，代码行更清楚，终端更亮

## 6. 验收结论约束

即使视觉效果更清晰，本次任务**不会**：

- 在代码或文档中写 `visually_accepted`
- 把这些 technique 标记为已通过人工视觉验收
- 进入 Style Sweep / Style Gallery

是否标记为 `visually_accepted` 必须在用户完成所有 5 个 technique 的浏览器观察后由后续任务决定。
