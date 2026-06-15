# V0.6.5 Card Stack 视觉强化报告

## 分支与 Commit

分支：`feature/v0.3.6-b1-shotplan-standardization`

## 背景

V0.6.4 已完成 UI 可见性：用户能在 `/video-lab/remotion-style-family` 页面点击按钮生成 Data News vs Card Stack 预览视频。

但 Card Stack 效果偏弱：
- prev card 只在主卡右下角露出一点边缘
- next card 不明显
- 短视频信息流感不够强

## 本轮目标

把 Card Stack 从"轻微叠层暗示"强化为"明显卡片堆叠 / 当前卡突出 / 下一张有预告感"。

## 修改文件

| 文件 | 变更 |
|------|------|
| `remotion/src/AiNewsVideo.tsx` | 强化 CardStackLayer 参数：prev/next card 偏移量、透明度、scale、添加 zIndex |
| `frontend/src/video-lab/pages/RemotionStyleFamilyPage.tsx` | 页面描述更新为 V0.6.5，差异说明更新为强化版 |

## 强化前问题（V0.6.4）

| 维度 | V0.6.4 值 | 问题 |
|------|-----------|------|
| prev card offsetX | 60 | 露出太小 |
| prev card offsetY | -40 | 露出太小 |
| prev card opacity | 0.5 | 太透明 |
| prev card scale | 0.88 | — |
| next card offsetX | -50 | 不够明显 |
| next card offsetY | 30 | 不够明显 |
| next card opacity | 0.3 | 太透明 |
| next card scale | 0.8 | — |
| current card offsetX | 20 | 偏右 |
| current card offsetY | 30 | 偏下 |
| current card scale | 0.92→1.0 | — |
| z-index | 无 | prev/current/next 层级不明确 |

## 参数调整说明

### prev card

| 参数 | V0.6.4 | V0.6.5 | 说明 |
|------|--------|--------|------|
| offsetX | 60 | 140 | 右移更远，右上角露出更明显 |
| offsetY | -40 | -80 | 上移更多 |
| opacity | 1.0→0.5 | 1.0→0.65 | 更不透明，叠层更清晰 |
| scale | 1.0→0.88 | 1.0→0.84 | 缩小更多表示更远 |

### next card

| 参数 | V0.6.4 | V0.6.5 | 说明 |
|------|--------|--------|------|
| offsetX | -50 | -120 | 左移更多 |
| offsetY | 30 | 70 | 下移更多 |
| opacity | 0.6→0.3 | 0.55→0.40 | 保持更清晰可见 |
| scale | 0.7→0.8 | 0.72→0.82 | 略大，预告感更强 |

### current card

| 参数 | V0.6.4 | V0.6.5 | 说明 |
|------|--------|--------|------|
| offsetX | 20→0 | 0 | 居中，不偏右 |
| offsetY | 30→0 | 0 | 居中，不偏下 |
| scale | 0.92→1.0 | 0.90→1.0 | 更大空间进入 |
| opacity | 0→1 | 0→1 | 不变 |

### zIndex

新增明确的 z-index 层：

```typescript
const zIndex = isPrev ? 1 : isNext ? 0 : 2;
// prev card: z=1 (behind)
// next card: z=0 (front preview)
// current card: z=2 (always on top)
```

这确保主卡永远在最上层，prev 在中间，next 在底层（被主卡遮住左下角，只露出右侧部分）。

## UI 验证方式

- **页面**：`/video-lab/remotion-style-family`
- **操作**：点击"生成对比预览"按钮
- **验证**：肉眼对比 Data News 和 Card Stack 两个 `<video controls>` 的效果

## Data News 对照结果

不受影响。Data News 走 `KeyPointCard` 单卡逻辑（`remotionFamily=data_news` 或未传），无 CardStackLayer 代码路径。

## Card Stack 强化后结果

预期在 UI 上可见的改进：

1. **prev card**（上一张）：主卡右上方有更明显的叠加边缘露出，offsetX=140, offsetY=-80，opacity=0.65
2. **next card**（下一张）：主卡左下方有更大的预览感，offsetX=-120, offsetY=70
3. **current card**：完全居中（offsetX=0, offsetY=0），主卡标题/正文/数字高亮保持清晰
4. **z-index 正确**：prev(1) < current(2) > next(0)，主卡始终在最上层

## 强化前后对比

| 维度 | V0.6.4 | V0.6.5 | 判断 |
|------|--------|--------|------|
| prev card 可见度 | 露出一点边角 | 右上明显露出叠加边缘 | ✅ 改进明显 |
| next card 可见度 | 不明显 | 左下有预览感 | ✅ 改进明显 |
| 主卡清晰度 | 偏右偏下 | 完全居中 | ✅ 改进 |
| 短视频信息流感 | 较弱 | 增强（三层卡片感） | ✅ 改进 |
| 字幕/正文干扰 | 无 | 无 | ✅ 无影响 |

## 当前问题

1. 主卡入场动效仍为简单淡入（`eased = 1 - Math.pow(1 - progress, 3)`），可进一步强化为从右侧滑入
2. next card 的 opacity 从 0.55→0.40（递减），在 entryWindow 末期几乎不可见，可考虑保持更高透明度

## 结论

### Card Stack 强化是否有效

**是**。V0.6.5 通过增大 prev/next card 的偏移量（offsetX/Y）、改善透明度、新增 z-index 管理，使三层卡片叠层感明显增强。

### 是否建议继续投入

**是**。当前主卡入场动效仍为简单淡入，建议下一轮强化主卡从右侧滑入的动效，进一步增强短视频感。

## 下一步建议

1. 主卡入场改为从右向左滑入（增强动效感）
2. next card 保持更高透明度（0.45 以上），使预览更持久
3. 考虑 prev card 的 border/background 样式差异化（目前 prev/current 使用相同 cardContent）
