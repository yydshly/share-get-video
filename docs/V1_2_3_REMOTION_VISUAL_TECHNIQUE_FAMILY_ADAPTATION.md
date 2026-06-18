# V1.2.7 — Visual Technique × Family Adaptation Matrix

## 1. 为什么需要 Family 适配测试

在 V1.2.6 之前，Visual Technique Matrix 只有一种模式：

```
1 family × 5 techniques = 5 clips
```

这个模式回答的问题是：**"在同一个版式下，哪种视觉技法更适配？"**

但我们还不知道另一个维度的问题：**"同一个视觉技法，换一种版式它还成立吗？"**

例如：

- `academic_sketch`（学术手绘草稿流）在 `data_news` 下看起来自然
- 但它在 `timeline_news`（时间线）下是否还像学术风格，而不是背景换皮？
- 或者它在 `caption_story`（大字叙事）下是否完全失去了学术感？

这就是 Family 适配测试要回答的问题。

## 2. 两种模式的区别

| | Technique 横向比较 | Family 适配测试 |
|---|---|---|
| 固定项 | family（默认 `data_news`） | technique（默认 `academic_sketch`） |
| 变化项 | 5 个 visualTechnique | 3 个 family |
| 矩阵形状 | 1 × 5 = 5 clips | 3 × 1 = 3 clips |
| 目的 | 判断哪种 technique 更适配当前 family | 判断某个 technique 换 family 后是否仍然成立 |
| 典型问题 | "blueprint 和 academic_sketch 哪个更适合这份 AI 评测内容？" | "academic_sketch 在时间线版式下还是学术风格吗，还是只是背景换皮？" |

两种模式都保留，用户可以切换。

## 3. 默认 3 个 family 的原因

Family 适配测试默认只使用 3 个 family：

```
data_news / timeline_news / caption_story
```

原因：

1. **MAX_MATRIX_ITEMS 限制**：后端有 `MAX_MATRIX_ITEMS = 9` 的保护，1×5 或 3×1 都在安全范围内
2. **避免组合爆炸**：如果做 5 family × 5 technique = 25 clips，每次渲染时间过长，不适合快速验证
3. **优先验证最有代表性的版式**：
   - `data_news`：数据驱动，最通用
   - `timeline_news`：时间线/流程型，有结构但不同于数据
   - `caption_story`：大字叙事型，完全不同方向

这三个版式覆盖了"数据型 / 结构型 / 叙事型"三个方向，能快速判断 technique 的版式适配范围。

## 4. 为什么不默认生成 5 family × 5 technique

如果一次性做完整的 5×5 = 25 clips：

- 渲染时间可能超过 2~3 分钟
- 不适合"快速验证"场景
- 人工难以同时比较 25 个结果

后续可以再做：

- **逐个 technique 过一遍 3 family**：用户选择一个 technique，快速看它在 3 个 family 下的表现
- **推荐默认 family**：根据 technique 的 `suitableFor` 属性推荐最适合的 family

但那是后续任务，本任务保持 3×1。

## 5. 5 个 technique 如何逐个适配 family

用户操作流程：

1. 切换到"Family 适配测试"模式
2. 从 technique 选择器中选一个（例如 `blueprint`）
3. 点击"运行视觉技法矩阵"
4. 看到 `blueprint` 在 `data_news` / `timeline_news` / `caption_story` 下的 3 个样片
5. 对每个样片标记：通过 / 部分通过 / 不通过 / 待验收
6. 切换下一个 technique，重复

这样 5 个 technique × 3 family = 15 clips，分 5 次运行，每次 3 clips，适合快速人工验收。

## 6. 本任务不改的内容

| 范围 | 状态 |
|------|------|
| 新增第 6 个 visualTechnique | ❌ 不做 |
| 改 Remotion 视觉实现 | ❌ 不做 |
| 改后端接口 | ❌ 不做 |
| 改 Style Sweep | ❌ 不做 |
| 改 Style Gallery | ❌ 不做 |
| 改 Recipe System | ❌ 不做 |
| 改 props_builder | ❌ 不做 |
| 改 VALID_VISUAL_TECHNIQUES | ❌ 不做 |
| 引入新依赖 | ❌ 不做 |
| 标记任何 technique 为 `visually_accepted` | ❌ 不做 |
| 数据库持久化 | ❌ 不做 |

本任务只改：

- `frontend/src/video-lab/pages/RemotionStyleFamilyPage.tsx`
- `docs/V1_2_3_REMOTION_VISUAL_TECHNIQUE_FAMILY_ADAPTATION.md`

## 7. UI 变化

在 Visual Technique Matrix 组件中：

1. **新增矩阵模式选择器**：两个按钮 [Technique 横向比较] [Family 适配测试]
2. **Technique 选择器**：在 Family 适配测试模式下显示，选中一个 technique
3. **矩阵规模标签**：动态显示 `1 family × 5 techniques = 5 clips` 或 `3 families × 1 technique = 3 clips`
4. **卡片增加 Family 说明**：在 Family 适配测试模式下，每个卡片显示当前 family 的描述和观察提示
5. **汇总区文案更新**：根据当前模式显示"Technique 横向比较"或"Family 适配测试"

## 8. 后续扩展

- [ ] technique × family 验收结果沉淀：根据验收结果，推荐每个 technique 的默认 family
- [ ] 推荐默认 family：根据 technique 的 `suitableFor` 属性，自动推荐最适合的 family
- [ ] 扩展 family 数量：增加到 4~5 个 family，覆盖更多版式类型
- [ ] Recipe 样片：进入后续 Style Sweep / Style Gallery 候选
