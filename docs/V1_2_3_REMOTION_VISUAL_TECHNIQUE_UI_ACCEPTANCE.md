# V1.2.3 Remotion Visual Technique UI Acceptance

## 1. 背景

V1.2.5+ 已实现 5 个 `visualTechnique`：

```text
academic_sketch
blueprint
data_viz_dashboard
agent_sandbox_25d
kinetic_code_typography
```

并已经接入 Visual Technique Matrix 工程链路：

```text
1 family × 5 visual techniques = 5 clips
```

工程上 5 个 technique 都已经能在 2s 冒烟预览下生成视频并 HTTP 200 访问。
但当前 UI 仍然只是一个"工程验证区"：

```text
- 卡片只显示 family × technique 参数名
- 用户不知道每个 technique 在视觉上代表什么
- 不知道应该观察什么
- 不知道生成成功 ≠ 视觉通过
- 没有任何本地人工验收能力
```

本次任务只改 UI 验收体验，**不**新增 visualTechnique，**不**改任何 Remotion 视觉实现细节。

## 2. 本次目标

把 Visual Technique Matrix 从"工程验证区"升级为"UI 人工验收区"：

- 提供每个 technique 的中文名、来源、描述、适合场景、观察点
- 显式说明当前是 2s 冒烟预览，不是完整视频
- 提供本地人工验收按钮（通过 / 部分通过 / 不通过）
- 提供本轮验收汇总（不写后端）
- 提供 2s / 6s / 12s 时长选择器（默认 2s）
- 显式说明"生成成功 ≠ 视觉通过"

## 3. 当前测试模式

| 字段 | 值 |
|---|---|
| 当前测试模式 | 2s 冒烟预览（Smoke Preview） |
| 当前 family | `data_news` |
| 矩阵规模 | 1 family × 5 visualTechnique = 5 clips |
| 目的 | 快速验证 5 种视觉技法是否能生成、能播放、能形成明显差异 |
| 限制 | 2s 样片不代表完整视频效果；生成成功不等于视觉通过 |
| 下一步 | 人工播放每个样片，标记通过 / 部分通过 / 不通过 |

## 4. 5 个 technique 元信息

### 4.1 academic_sketch — 学术手绘草稿流

- 来源：Effect Prototype Gallery / academic
- 状态：asset_verified
- 验收：visually_unaccepted
- 描述：米白纸张、网格线、手绘批注，用于论文解读、AI 原理解释、研究报告摘要
- 适合：论文解读、AI 原理解释、研究报告摘要、知识类短视频
- 观察点：
  - 米白纸张是否明显
  - 网格线是否可见
  - 是否有手绘批注
  - 正文是否可读

### 4.2 blueprint — 工程蓝图晒图风

- 来源：Effect Prototype Gallery / blueprint
- 状态：asset_verified
- 验收：visually_unaccepted
- 描述：深蓝晒图纸、工程网格、角标记，用于架构解析、系统设计、技术规格说明
- 适合：架构解析、系统设计、技术规格、工程原理
- 观察点：
  - 蓝图感是否明显
  - 工程网格是否可见
  - 角标记是否可见
  - 正文是否可读

### 4.3 data_viz_dashboard — 数据动态看板

- 来源：Effect Prototype Gallery / dataviz
- 状态：asset_verified
- 验收：visually_unaccepted
- 描述：动态图表、柱状图、折线图、圆环图和指标 chip，用于 Benchmark、模型对比、产品数据
- 适合：AI Benchmark、模型能力对比、产品数据、性能报告
- 观察点：
  - 是否像数据看板
  - 图表元素是否明显
  - 指标 chip 是否可见
  - 正文是否可读

### 4.4 agent_sandbox_25d — 智能体沙盒模拟

- 来源：Effect Prototype Gallery / sandbox
- 状态：asset_verified
- 验收：visually_unaccepted
- 描述：2.5D 空间、Agent 节点、连接线和数据包，用于多智能体协作、工作流、系统架构说明
- 适合：Agent 工作流、多智能体协作、AI 自动化流程、系统架构
- 观察点：
  - 节点是否明显
  - 连接线是否可见
  - 是否有数据包流动
  - 是否有系统沙盒感

### 4.5 kinetic_code_typography — 动态代码排版

- 来源：Effect Prototype Gallery / typography
- 状态：asset_verified
- 验收：visually_unaccepted
- 描述：IDE 背景、代码行、语法高亮、终端日志和光标闪烁，用于开发者内容、API 讲解、代码教程
- 适合：开发教程、API 讲解、代码片段解释、开源项目摘要
- 观察点：
  - 是否像代码编辑器
  - 代码行是否可见
  - 终端日志是否可见
  - 正文是否可读

## 5. 本地人工验收（UI ephemeral）

### 5.1 状态机

```ts
type LocalVisualAcceptance = "pending" | "accepted" | "partial" | "rejected";
```

| 状态 | 文案 | 颜色 |
|---|---|---|
| pending | 待验收 | 灰 |
| accepted | 通过 | 绿 |
| partial | 部分通过 | 琥珀 |
| rejected | 不通过 | 红 |

### 5.2 关键约束

```text
- 本地验收状态只保存在前端 useState，刷新即丢失
- 不写后端
- 不影响后端 visualTechniqueMatrix 接口
- 不进入 Style Sweep
- 不进入 Style Gallery
- 不标记 visually_accepted
```

### 5.3 key 命名

```ts
const key = `${item.family}-${item.visualTechnique}`;
```

例如 `data_news-academic_sketch`。

## 6. 时长选择器

UI 上提供 `2s / 6s / 12s` 三个按钮：

| 时长 | 性质 | 说明 |
|---|---|---|
| 2s | 冒烟预览 | 当前默认；快速验证生成和差异 |
| 6s | 视觉预览 | 验证动效、可读性和节奏 |
| 12s | 长预览 | 完整动效观察 |

注意：选择不同时长后，需要重新点击"运行视觉技法矩阵"按钮触发后端渲染。

## 7. 验收汇总

矩阵下方和卡片列表上方各显示一次本轮汇总：

```text
视觉验收汇总：
通过：x
部分通过：x
不通过：x
待验收：x
```

明确说明：

```text
当前汇总仅保存在前端页面刷新前，用于本轮人工观察
```

## 8. 扩展路径

```text
1. 2s 冒烟预览：验证是否能生成和形成差异（当前已实现）
2. 6~8s 视觉预览：验证动效、可读性和节奏（未来）
3. 单 technique × 多 family：验证适配不同版式（未来）
4. 完整 Recipe 样片：进入后续 Style Sweep / Style Gallery 候选（未来）
```

注意：本次**不**实现 6~8s 视觉预览的视觉验收增强，**不**进入 Recipe 阶段。

## 9. 文案约束

UI 上**避免**出现以下措辞：

```text
已通过
已验收
可进入 Gallery
正式可用
```

只允许出现：

```text
生成成功
待视觉验收
本地验收记录
```

目的：让用户明确区分"工程生成成功"和"视觉验收通过"两个不同阶段。

## 10. 改动文件

| 文件 | 改动 |
|---|---|
| `frontend/src/video-lab/pages/RemotionStyleFamilyPage.tsx` | 重写 VisualTechniqueVariantMatrix 组件；新增 `visualTechniqueClipSeconds` state |

未改动：

- Style Sweep
- Style Gallery
- Recipe System
- 任何 visualTechnique 视觉实现
- 后端
- 数据库

## 11. 验收结果

| 维度 | 状态 |
|---|---|
| `npm run build` | ✅ 通过 |
| 5 technique 中文名 + 描述 | ✅ |
| 5 technique 适合场景 chips | ✅ |
| 5 technique 观察点列表 | ✅ |
| "生成成功 ≠ 视觉通过" 提示 | ✅（smoke preview 卡片 + 卡片内 "视觉：待人工验收"） |
| 本地人工验收按钮（通过/部分通过/不通过） | ✅ |
| 验收汇总（通过/部分通过/不通过/待验收） | ✅ |
| 2s 冒烟预览说明 | ✅（smoke preview 卡片 + 时长选择器提示） |
| 6s / 12s 时长选择器 | ✅ |
| 扩展路径说明 | ✅（矩阵底部） |

## 12. 当前结论

5 个 `visualTechnique` 在 UI 上已经具备：

- 可理解的中文名 + 来源
- 可读的描述、适合场景、观察点
- 可执行的本地人工验收按钮
- 可观察的本轮汇总
- 可切换的 2s / 6s / 12s 时长

UI 已经从"工程验证区"升级为"UI 人工验收区"。

本任务**不**为视觉验收背书，**不**把它们标记为 `visually_accepted`。
是否标记 `visually_accepted` 必须在人工完成所有 5 个 technique 的浏览器观察后由后续任务决定。
