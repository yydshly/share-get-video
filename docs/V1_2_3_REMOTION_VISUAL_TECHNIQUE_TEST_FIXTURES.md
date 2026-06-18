# V1.2.3 — Visual Technique Test Fixtures

## 1. 为什么当前单一测试内容不够

在 V1.2.5 之前，Visual Technique Matrix 只使用一段通用的 AI 评测文案：

```
研究显示，新一代 AI 模型在多模态理解、工具调用和复杂推理任务上都有显著提升，
但评测指标仍然难以完整衡量真实智能。
```

这段文案适合"冒烟测试"（验证 5 个 technique 是否都能生成），但不适合判断每个 technique 的视觉语义适配度。

例如：

- `academic_sketch`（学术手绘草稿流）需要真正带有"推理过程""研究结论"的内容，才能看出纸张网格+手写批注是否自然
- `blueprint`（工程蓝图晒图风）需要系统架构、模块关系的文案，才能看出蓝图网格+角标是否有内容可依附
- `kinetic_code_typography`（动态代码排版）需要代码流程、API 步骤，才能看出 IDE 背景+语法高亮是否有意义

用通用文案测试所有 technique，等于把所有 technique 都放在"不适配"的内容下，无法真正验证它们的视觉语义是否成立。

## 2. Test Fixture 方案

新增 6 个测试内容模式（Test Fixture），每个 fixture 包含：

| 字段 | 说明 |
|------|------|
| `name` | 中文显示名 |
| `purpose` | 这个 fixture 的测试目的 |
| `recommendedTechniques` | 推荐使用该内容测试的 technique 列表 |
| `content` | 实际发送给 Remotion 的测试文案 |

### 6 个 Fixture 一览

| ID | 名称 | 推荐 technique | 核心内容主题 |
|----|------|---------------|-------------|
| `generic_ai_eval` | 通用 AI 评测 | 全部（冒烟用） | AI 模型多维能力提升，评测指标局限 |
| `academic_explainer` | 学术解释 | `academic_sketch` | AI 评测为何越来越难，推理过程的重要性 |
| `blueprint_architecture` | 工程架构 | `blueprint`, `agent_sandbox_25d` | Agent 系统四层架构，消息通道连接 |
| `data_dashboard` | 数据看板 | `data_viz_dashboard` | 模型 A 多维度指标提升，Benchmark 数据 |
| `agent_sandbox` | Agent 沙盒 | `agent_sandbox_25d` | Planner/Model/Tool/Memory 协作与重规划 |
| `code_typography` | 代码教程 | `kinetic_code_typography` | 模型 API 调用步骤，错误处理重要性 |

### Fixture 详细内容

#### `generic_ai_eval` — 通用 AI 评测
- **目的**：通用横向比较，适合快速冒烟测试
- **推荐 technique**：全部
- **content**：研究显示，新一代 AI 模型在多模态理解、工具调用和复杂推理任务上都有显著提升，但评测指标仍然难以完整衡量真实智能。

#### `academic_explainer` — 学术解释
- **目的**：测试 academic_sketch 是否适合解释概念、推理过程、研究摘要
- **推荐 technique**：`academic_sketch`
- **content**：为什么 AI 评测越来越难？过去只看最终答案，现在还要看推理过程、工具调用和失败修正。真正的评测像观察学生解题，而不是只看分数。

#### `blueprint_architecture` — 工程架构
- **目的**：测试 blueprint 是否适合系统架构、模块关系、工程流程
- **推荐 technique**：`blueprint`, `agent_sandbox_25d`
- **content**：一个 AI Agent 系统由四层组成：输入层接收任务，规划层拆解步骤，工具层执行动作，记忆层保存上下文。各层通过消息通道连接，形成可追踪的执行链路。

#### `data_dashboard` — 数据看板
- **目的**：测试 data_viz_dashboard 是否适合 Benchmark、模型对比、产品数据
- **推荐 technique**：`data_viz_dashboard`
- **content**：模型 A 在多模态理解上提升 24%，工具调用成功率达到 87%，长上下文任务成本下降 31%。这些指标说明模型能力正在从单点问答转向系统级表现。

#### `agent_sandbox` — Agent 沙盒
- **目的**：测试 agent_sandbox_25d 是否适合多智能体协作、工具调用、工作流解释
- **推荐 technique**：`agent_sandbox_25d`
- **content**：Planner 负责拆解任务，Model 负责生成方案，Tool 负责执行外部动作，Memory 负责记录状态。多个 Agent 通过消息通道协作，并在失败时重新规划。

#### `code_typography` — 代码教程
- **目的**：测试 kinetic_code_typography 是否适合 API 讲解、代码流程、开发者内容
- **推荐 technique**：`kinetic_code_typography`
- **content**：调用模型 API 的核心步骤包括：构造 request，发送 prompt，解析 response，处理错误，并将日志写入终端。稳定的错误处理比一次成功调用更重要。

## 3. recommendedTechniques 的含义

`recommendedTechniques` 表示"这个 fixture 的内容在语义上最匹配哪些 technique"。

这不意味着选择了"代码教程"fixture 就只生成 `kinetic_code_typography`。**本任务仍然生成全部 5 个 technique**，目的是：

> 在同一内容模式下，横向对比 5 个 technique 的适配度，让用户判断哪个 technique 在该内容下看起来最自然。

如果某个 technique 在非推荐 fixture 下看起来不自然，这是预期行为，不算 bug。

## 4. 为什么本任务仍然生成 1×5，而不是自动过滤 technique

验收维度需要横向对比。场景是：

> 给定同一段内容（代码教程），哪个视觉技法最适合呈现它？

如果只生成 1 个 technique，就失去了横向对比的参考基准。后续可以再做：

- **推荐 technique 单项测试**：给定内容，自动选择最适配的 1 个 technique 做深度验证
- **单 technique × 多 family**：验证某个 technique 在不同版式下的表现

但那是后续任务，本任务不做。

## 5. 本任务不改的内容

| 范围 | 状态 |
|------|------|
| 新增第 6 个 visualTechnique | ❌ 不做 |
| 改 Remotion 视觉实现 | ❌ 不做 |
| 改 Style Sweep | ❌ 不做 |
| 改 Style Gallery | ❌ 不做 |
| 改 Recipe System | ❌ 不做 |
| 改后端接口 | ❌ 不做 |
| 改 props_builder | ❌ 不做 |
| 改 VALID_VISUAL_TECHNIQUES | ❌ 不做 |
| 引入新依赖 | ❌ 不做 |
| 标记任何 technique 为 `visually_accepted` | ❌ 不做 |
| 数据库持久化 | ❌ 不做 |

本任务只改：

- `frontend/src/video-lab/pages/RemotionStyleFamilyPage.tsx`
- `docs/V1_2_3_REMOTION_VISUAL_TECHNIQUE_TEST_FIXTURES.md`

## 6. UI 变化

在 Visual Technique Matrix 组件中：

1. **新增测试内容选择器**：6 个按钮横向排列，选中后高亮
2. ** Fixture 信息卡**：显示名称、目的、推荐 technique、测试文案预览（最多 2 行）
3. **卡片增加内容匹配标签**：每个 technique 卡片显示"内容匹配：推荐"或"内容匹配：非推荐，仅作横向对比"
4. **文案提示**：强调"测试内容会影响视觉判断"

## 7. 后续扩展

- [ ] 单 technique × 多 family：验证某个 technique 在不同版式下的表现
- [ ] 推荐 technique 单项测试：给定内容，自动选择最适配的 1 个 technique 做深度验证
- [ ] 6s/12s 长预览：在更长的时间尺度上验证动效和节奏
- [ ] Recipe 样片：进入后续 Style Sweep / Style Gallery 候选
