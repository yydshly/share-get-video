# V1.2.3: Visual Technique Content Probe Layer

## 为什么 6s 仍然看不出差异

在 `V1.2.3-style-gallery-validation-center` 分支的早期人工验收中，即使用户选择：

- **Family 适配测试**模式
- **academic_explainer** fixture
- **6s 视觉预览**
- 三个不同 family：`data_news` / `timeline_news` / `caption_story`

观察结论是：三个 family 看起来仍然是**同一个背景**，没有足够标题、正文、步骤、结构差异。

### 根因分析

问题不在于时长（6s 已经足够），而在于：

1. **Visual Technique Matrix 缺少显性的内容探针层**。`visualTechnique` 目前主要影响背景层（`BackgroundLayer` + `AcademicSketchLayer` 等），但没有把 fixture 内容结构化地展示出来。
2. **背景变化 vs 内容结构差异无法区分**。当用户看到两个看起来相似的深色/网格/极光背景时，无法判断这是"背景换皮"还是"内容结构真的有差异"。

## 背景层 vs 内容层的区别

| 层次 | 控制参数 | 作用 |
|------|---------|------|
| 背景层 | `visualTechnique` (academic_sketch / blueprint / data_viz_dashboard / ...) | 改变整体视觉氛围（纸张/蓝图/仪表盘/代码编辑器） |
| **内容探针层** | `visualTechniqueContentProbe=true` | 强制在画面上叠加标题、要点、family 结构标签，让 reviewer 能区分"背景换皮"和"结构差异" |

背景层是被动的——它定义了视觉基调，但相同的要点标题在不同的背景上仍然难以区分。

内容探针层是主动的——它把当前视频的**标题**、**3 个要点**、**family 标签**、**technique 标签**、**fixture 标签**全部渲染出来，让不同 family 的内容结构一目了然。

## `visualTechniqueContentProbe` 的用途

**仅限 Visual Technique Matrix 人工验收使用**，不是通用生成参数。

当 `style.visualTechniqueContentProbe === true` 时，`AiNewsVideo` 额外渲染一个 `VisualTechniqueContentProbeLayer`（z-index=50），覆盖在所有内容之上。

**普通视频生成不受影响**——即使误传了 `visualTechniqueContentProbe=true`，该层也只渲染在 Visual Technique Matrix 产生的样片上，不影响 Style Sweep、Style Gallery 或普通 API 调用。

## family 对内容结构的影响

`VisualTechniqueContentProbeLayer` 根据 `remotionFamily` 渲染不同的内容布局：

### `data_news` — 信息卡片

```
┌─────────────────────────────────────┐
│ PROBE · TECHNIQUE                  │
│ [大标题]                            │
│                                     │
│ ┌───────────────────────────────┐  │
│ │ ① [要点一]                    │  │
│ └───────────────────────────────┘  │
│ ┌───────────────────────────────┐  │
│ │ ② [要点二]                    │  │
│ └───────────────────────────────┘  │
│ ┌───────────────────────────────┐  │
│ │ ③ [要点三]                    │  │
│ └───────────────────────────────┘  │
│                                     │
│ [DATA_NEWS] [ACADEMIC_SKETCH]      │
│          [ACADEMIC_EXPLAINER]       │
└─────────────────────────────────────┘
```

### `timeline_news` — 时间线

```
┌─────────────────────────────────────┐
│ PROBE · FAMILY ADAPT               │
│ [大标题]                            │
│                                     │
│  ●─ STEP 1  [要点一]                │
│  │                                  │
│  ●─ STEP 2  [要点二]                │
│  │                                  │
│  ●─ STEP 3  [要点三]                │
│                                     │
│ [TIMELINE_NEWS] [BLUEPRINT]         │
└─────────────────────────────────────┘
```

### `caption_story` — 大字叙事

```
┌─────────────────────────────────────┐
│ PROBE · TECHNIQUE                  │
│ [大标题]                            │
│                                     │
│         [要点一 — 核心叙事]           │
│   ─────────────────────            │
│         [要点二]                     │
│         [要点三]                     │
│                                     │
│ [CAPTION_STORY] [KINETIC_CODE]      │
└─────────────────────────────────────┘
```

## technique 对内容表达的影响

ContentProbeLayer 不为每个 technique 做复杂模板，但提供轻量差异：

| technique | chip 颜色 | 特点 |
|-----------|----------|------|
| `academic_sketch` | 米白底 + 棕色边框 | 便签感、手写圈点暗示 |
| `blueprint` | 深蓝底 + 青色边框 | 工程框图感、连接线暗示 |
| `data_viz_dashboard` | 深色底 + 青色边框 | 指标 chip 暗示、数据高亮 |
| `agent_sandbox_25d` | 深紫底 + 紫色边框 | 节点关系暗示、Planner/Model/Tool/Memory 标签暗示 |
| `kinetic_code_typography` | 暗色底 + 绿松石边框 | 代码行暗示、伪代码步骤暗示 |

## 该 probe 是 lab-only，不进入正式生成链路

### 边界约束

- ❌ 不新增 visualTechnique
- ❌ 不改 Style Sweep
- ❌ 不改 Style Gallery
- ❌ 不做 Recipe System
- ❌ 不引入新依赖
- ❌ 不把任何结果标记为 `visually_accepted`
- ❌ 不改变普通视频生成的默认表现
- ❌ 不改 `MAX_MATRIX_ITEMS`
- ❌ 不做数据库持久化

### 仍不标记 `visually_accepted`

所有通过 ContentProbeLayer 渲染的样片仍然是 lab-only 临时资产。

## 新增参数

```ts
// remotion/src/data.ts — RemotionStyle 扩展
visualTechniqueContentProbe?: boolean;
visualTechniqueFixtureId?: string;
visualTechniqueMatrixMode?: "technique_compare" | "family_adaptation";
```

```python
# app/video_lab/renderers/remotion/props_builder.py — 白名单透传
if params.get("visualTechniqueContentProbe") is True:
    style["visualTechniqueContentProbe"] = True

fixture_id = params.get("visualTechniqueFixtureId")
if isinstance(fixture_id, str):
    style["visualTechniqueFixtureId"] = fixture_id

matrix_mode = params.get("visualTechniqueMatrixMode")
if matrix_mode in ("technique_compare", "family_adaptation"):
    style["visualTechniqueMatrixMode"] = matrix_mode
```

```ts
// frontend — 仅 Visual Technique Matrix 请求发送
params: {
  // ...
  visualTechniqueContentProbe: true,
  visualTechniqueFixtureId: visualTechniqueFixtureId,
  visualTechniqueMatrixMode: visualTechniqueMatrixMode,
}
```

## 实现文件

| 文件 | 变更 |
|------|------|
| `remotion/src/data.ts` | `RemotionStyle` 新增 3 个可选字段 |
| `remotion/src/AiNewsVideo.tsx` | 新增 `VisualTechniqueContentProbeLayer` 组件；在 `AiNewsVideo` 中条件渲染 |
| `app/video_lab/renderers/remotion/props_builder.py` | 白名单透传 3 个 lab-only 参数 |
| `frontend/src/video-lab/pages/RemotionStyleFamilyPage.tsx` | `runVisualTechniqueMatrix` 发送 probe 参数；UI 文案增加"内容探针：已开启" |
| `tests/test_style_family_visual_technique_matrix.py` | 新增 4 个测试覆盖 probe 参数透传 |
| `docs/V1_2_3_REMOTION_VISUAL_TECHNIQUE_CONTENT_PROBE.md` | 本文档 |

## 用户 UI 验收观察点

启用内容探针层后，在 Visual Technique Matrix 中观察：

1. **标题是否明显** — 左上角大标题是否在缩略图中可见
2. **3 个要点是否清晰** — data_news 的编号卡片 / timeline_news 的时间线步骤 / caption_story 的叙事排版是否明显不同
3. **family 标签差异** — `DATA_NEWS` / `TIMELINE_NEWS` / `CAPTION_STORY` 三个 chip 是否清晰可辨
4. **technique 标签** — `ACADEMIC_SKETCH` / `BLUEPRINT` / `DATA_VIZ_DASHBOARD` 等是否正确显示
5. **fixture 标签** — `ACADEMIC_EXPLAINER` / `BLUEPRINT_ARCHITECTURE` 等是否正确显示
6. **三个 family 的内容布局是否真正不同** — 这是关键验收点：如果三个 family 的内容探针布局看起来仍然相似，说明问题不只是背景，而是需要更深的 family 模板区分
