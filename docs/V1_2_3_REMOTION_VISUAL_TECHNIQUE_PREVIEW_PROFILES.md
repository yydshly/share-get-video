# V1.2.8 — Visual Technique Preview Profiles

## 1. 为什么 2s 不适合作视觉验收

在 V1.2.7 之前，Visual Technique Matrix 默认使用 2s 时长。虽然 UI 上有 2s/6s/12s 三个按钮，但：

1. **默认是 2s**：用户容易直接用 2s 做"验收"，而 2s 只能看到开头一帧
2. **2s 内容密度不足**：只展示前 2 个 keyPoint，看不出完整动效和节奏
3. **UI 没有明确区分用途**：三个时长按钮只是数字不同，没有说明各自的适用场景

结果是：用户认为"能生成 2s 视频 = 视觉验收通过"，而实际上 2s 根本无法判断 technique 的视觉适配度。

## 2. 三个 Preview Profile 的定位

| Profile | clipSeconds | keyPointCount | Badge | 定位 |
|---------|------------|---------------|-------|------|
| `smoke_2s` | 2 | 2 | Smoke | 快速冒烟：验证能生成、能播放、背景方向大致不同 |
| `visual_6s` | 6 | 3 | Review | **默认**：适合人工视觉验收，观察版式、可读性、特征是否展开 |
| `deep_12s` | 12 | 4 | Deep | 深度观察：完整动效、转场节奏、内容承载能力，适合 Recipe 候选前的判断 |

### 为什么 6s 是默认

- 2s 太短，看不出 technique 特征是否真正展开
- 12s 渲染耗时，不适合作为每次修改后的快速验证
- 6s 刚好：能展示 3 个 keyPoint，能观察 technique 的完整节奏，渲染时间可接受

## 3. clipSeconds 与 keyPointCount 对应关系

```ts
smoke_2s:   { clipSeconds: 2,  keyPointCount: 2 }  // 内容密度低，只够冒烟
visual_6s:  { clipSeconds: 6,  keyPointCount: 3 }  // 平衡：足够观察又不至于太长
deep_12s:   { clipSeconds: 12, keyPointCount: 4 }  // 完整内容，适合深度验证
```

V1.2.7 之前 `keyPointCount` 固定为 2，6s 和 12s 下内容密度不足。V1.2.8 改为 profile 内联动。

## 4. stale result 提示的原因

用户切换选项后，旧结果仍然显示在页面上，容易被误认为当前参数下的结果。

V1.2.8 增加了 `resultSignature` 机制：

1. 每次运行前记录当前参数签名（mode + fixtureId + previewProfileId + adaptationTechnique）
2. 成功返回后保存签名
3. 渲染时比较当前参数签名与保存的签名
4. 不一致时显示警告：**"当前结果来自旧参数。请重新运行后再验收。"**

这样用户清楚知道：切换参数后需要重新运行，旧结果不能作为当前参数的验收依据。

## 5. UI 变化

### 预览档位选择器

在矩阵顶部显示 3 个档位按钮，每个按钮带有 hover 提示说明用途。当前选中项高亮紫色。

### 档位信息卡

在测试内容 fixture info 下方，显示当前档位的详细信息：

- 档位名称 + Badge（Smoke / Review / Deep）
- clipSeconds 和 keyPointCount
- 用途说明
- 警告文案（2s 和 12s 有特殊提示）

### 运行按钮动态化

按钮文案根据当前档位动态变化：
- `运行 2s 冒烟预览`
- `运行 6s 视觉预览`
- `运行 12s 深度预览`

loading 时：`正在生成 6s 视觉预览...`

### 卡片增加档位标注

每个视频卡片的状态栏右侧显示：
- `6s 视觉预览 · 3 points`（或对应档位）

### 2s 下的验收按钮警告

在 2s 冒烟预览下，验收按钮下方显示警告文案：
> ⚠ 2s 仅为冒烟预览，请谨慎标记通过，最终结论请使用 6s/12s。

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
- `docs/V1_2_3_REMOTION_VISUAL_TECHNIQUE_PREVIEW_PROFILES.md`

## 7. 后续扩展

- [ ] 12s Recipe 候选样片：基于 deep_12s 档位的结果，沉淀为 Style Gallery 候选
- [ ] technique × family 验收记录沉淀：根据验收结果，推荐每个 technique 的默认 family 和默认 preview profile
- [ ] 默认推荐 profile：根据 technique 类型推荐默认 profile（部分 technique 可能默认 deep_12s 更合适）
