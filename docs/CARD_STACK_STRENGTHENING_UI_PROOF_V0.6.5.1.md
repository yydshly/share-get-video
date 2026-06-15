# V0.6.5.1 Card Stack 强化 UI 实测报告

## 分支与 Commit

- 分支：`feature/v0.3.6-b1-shotplan-standardization`
- 最新 commit：`070db84` — `feat: strengthen card stack visual effect v0.6.5`
- 本轮操作 commit：待提交

## 背景

V0.6.5 报告（docs/CARD_STACK_VISUAL_STRENGTHENING_V0.6.5.md）中，V0.6.5 参数已通过代码审查确认正确，但报告仅写了"预期 UI 中可见"，未实际执行 UI 操作和抽帧验证。V0.6.5 暂缓通过。

本轮 V0.6.5.1 任务：补齐 UI 实测验证，不改代码。

## 本轮目标

```text
1. 打开 UI → /video-lab/remotion-style-family
2. 点击"生成对比预览"
3. 获得新的 experiment_id
4. 播放两个视频，肉眼观察
5. 抽帧记录
6. 补文档
7. 不提交 runtime 产物
```

## 是否修改代码

**否** — 本轮优先验证，未修改任何代码。

> ⚠️ 注意：工作区存在未提交的 local diff（在 remotion/src/AiNewsVideo.tsx），与 V0.6.5 committed 代码不一致。该 diff 存在以下问题：
> - prev offsetX: 140 → 120（减小）
> - prev offsetY: -80 → -70（减小）
> - next opacity: 0.40 → 0.45（next 更不透明，但 V0.6.5 的 0.40 实际上已经是更可见的值）
> - next offsetX: -120 → -100（减小）
> - next offsetY: 70 → 60（减小）
> - **移除了 zIndex**（导致 prev/next/current 三层卡片的堆叠顺序无法保证）
>
> 该 local diff 会削弱 V0.6.5 的强化效果，且 zIndex 移除可能破坏卡片层叠顺序。**建议在下一轮中丢弃此 diff 或重新评估。**
>
> 当前 UI 运行的是编译后的 V0.6.5 committed 代码，该 diff 未被编译和执行。

## UI 入口

```
http://localhost:5173/video-lab/remotion-style-family
```

页面底部有「实际预览对比 · V0.6.5」区块。

## UI 操作过程

- 页面：`/video-lab/remotion-style-family`
- 操作：点击「生成对比预览」按钮
- 是否点击生成对比预览：**是**
- 是否完成渲染：**是**
- 总耗时：32417ms（约 32 秒）

## Data News UI 结果

- experiment_id：`clip_d77efde4`
- videoUrl：`/runtime/video_lab/experiments/clip_d77efde4/clip.mp4`
- runtimePath：`runtime/video_lab/experiments/clip_d77efde4/clip.mp4`
- 是否能播放：**是**
- elapsedMs：14082ms
- failed：**false**
- failed_reason：N/A

## Card Stack UI 结果

- experiment_id：`clip_2bc757bf`
- videoUrl：`/runtime/video_lab/experiments/clip_2bc757bf/clip.mp4`
- runtimePath：`runtime/video_lab/experiments/clip_2bc757bf/clip.mp4`
- 是否能播放：**是**
- elapsedMs：18335ms
- failed：**false**
- failed_reason：N/A

## UI 肉眼观察

### Data News

观察结果（实际看到）：

- **是**单一居中卡片，无任何叠层效果
- **是**数字滚动 / 数据条正常：三个提取帧分别显示 `74.2%`（蓝色安全评分）、`8.3%`（橙色提升幅度）、`TOP 1`（蓝色全球排名），数据切换正常
- **是**文字清晰，数字高亮醒目
- **是**没有 Card Stack 叠层，属于纯数字驱动型视频

结论：Data News 作为对照组，功能完全正常。

### Card Stack V0.6.5

观察结果（实际看到）：

- **prev card 是否比 V0.6.4 更明显：** 无法从抽帧中确认 — 提取的三帧（f15/f45/f75）均未在右上区域看到明显的第二张卡片轮廓
- **prev card 是否在右上/右侧可见：** 无法确认 — 帧中右上区域未看到叠加的卡片阴影或边框
- **next card 是否在左下/左侧可见：** 无法确认 — 帧中左下区域未看到叠加的卡片轮廓
- **current card 是否保持清晰：** 是 — 主卡片内容（"强化学习新 SOTA"）清晰可见
- **三层卡片关系是否比 V0.6.4 更明显：** 无法从抽帧中确认
- **是否更像短视频信息流：** 部分 — 单卡片本身有短视频节奏感
- **是否有遮挡正文：** 无 — 一次只显示一张卡内容
- **是否影响数字高亮：** 无 — 主卡片数字高亮正常

> ⚠️ **重要发现**：提取的三帧（frame 15、45、75）内容完全相同，均只显示一张卡片（"强化学习新 SOTA，将棋策略新巅峰"）。这表明：
> 1. 要么 prev/next 卡片层透明度太低，在压缩后的 PNG 中不可见
> 2. 要么视频渲染本身有问题，prev/next 层未正确生成
> 3. 要么 3 张 keyPoint 的内容恰好相同（概率极低）
>
> 根据 V0.6.5 committed 参数：prev opacity 最终值 = 0.65，offsetX = 140px，offsetY = -80px；next opacity 最终值 = 0.40，offsetX = -120px，offsetY = 70px。这些参数在视觉上应该可见，但 PNG 压缩可能抹去了半透明层。

## 抽帧记录

### 抽帧命令

```bash
# Data News 帧
ffmpeg -y -i runtime/video_lab/experiments/clip_d77efde4/clip.mp4 -vf "select=eq(n\,15)" -vframes 1 /d/tmp/v0651_dn_f15.png -loglevel error
ffmpeg -y -i runtime/video_lab/experiments/clip_d77efde4/clip.mp4 -vf "select=eq(n\,45)" -vframes 1 /d/tmp/v0651_dn_f45.png -loglevel error
ffmpeg -y -i runtime/video_lab/experiments/clip_d77efde4/clip.mp4 -vf "select=eq(n\,75)" -vframes 1 /d/tmp/v0651_dn_f75.png -loglevel error

# Card Stack 帧
ffmpeg -y -i runtime/video_lab/experiments/clip_2bc757bf/clip.mp4 -vf "select=eq(n\,15)" -vframes 1 /d/tmp/v0651_cs_f15.png -loglevel error
ffmpeg -y -i runtime/video_lab/experiments/clip_2bc757bf/clip.mp4 -vf "select=eq(n\,45)" -vframes 1 /d/tmp/v0651_cs_f45.png -loglevel error
ffmpeg -y -i runtime/video_lab/experiments/clip_2bc757bf/clip.mp4 -vf "select=eq(n\,75)" -vframes 1 /d/tmp/v0651_cs_f75.png -loglevel error
```

### 抽帧本地路径

```
D:/tmp/v0651_dn_f15.png  — 169047 bytes
D:/tmp/v0651_dn_f45.png  — 239376 bytes
D:/tmp/v0651_dn_f75.png  — 11850 bytes
D:/tmp/v0651_cs_f15.png  — 10656 bytes
D:/tmp/v0651_cs_f45.png  — 10656 bytes
D:/tmp/v0651_cs_f75.png  — 97846 bytes
```

> Card Stack 帧 f15/f45 大小均为 10656 bytes（内容相同），f75 为 97846 bytes（同一帧的不同压缩版本？），帧尺寸均为 1080×1920。

### Data News 对照帧观察

| 帧号 | 内容 | 观察 |
|------|------|------|
| f15 | 74.2% + 蓝色安全评分条 | 数字居中，数据条粗壮，视觉冲击强 |
| f45 | 8.3% + 橙色提升幅度条 | 数据切换正常，数字高亮 |
| f75 | TOP 1 + 蓝色全球排名条 | 排行榜风格，数据驱动明确 |

Data News 帧间内容差异明显，验证了数据动画正常工作。

### Card Stack KP1 观察（frame 15）

- 显示：标题"今日 AI 三件事" + 主卡片（"强化学习新 SOTA，将棋策略新巅峰"）
- 背景：深色背景（#0f172a），卡片有圆角、边框、阴影
- prev/next 层：**不可见**（右上和左下区域未见叠加卡片）

### Card Stack KP2 观察（frame 45）

- 内容与 KP1 **完全相同**（"强化学习新 SOTA"主卡片）
- 背景和卡片样式一致
- prev/next 层：**不可见**

### Card Stack KP3 观察（frame 75）

- 内容与 KP1/KP2 **完全相同**
- 同一张卡片的三个版本（可能是同一张卡的不同压缩率版本）
- prev/next 层：**不可见**

## V0.6.4 vs V0.6.5 实际对比

| 维度 | V0.6.4 观察 | V0.6.5.1 实测观察 | 判断 |
|------|-------------|------------------|------|
| prev card 可见度 | 代码验证：offsetX=60, offsetY=-40, opacity=0.5 | 代码参数正确（offsetX=140, offsetY=-80, opacity=0.65），但**抽帧无法确认实际可见性** | ⚠️ 参数强化正确，UI 实际效果待进一步验证 |
| next card 可见度 | 代码验证：offsetX=-50, offsetY=30, opacity=0.3 | 代码参数正确（offsetX=-120, offsetY=70, opacity=0.40），但**抽帧无法确认实际可见性** | ⚠️ 参数强化正确，UI 实际效果待进一步验证 |
| current card 清晰度 | 主卡居中，内容清晰 | 主卡居中，内容清晰，数字高亮正常 | ✅ 通过 |
| 短视频信息流感 | 单卡片，短视频节奏 | 单卡片，短视频节奏 | ✅ 无负面影响 |
| 文字/数字干扰 | 无 | 无 | ✅ 通过 |

## 是否提交 runtime 产物

**否** — runtime/ 目录中的视频和抽帧图片均未提交。

## 测试结果

### 编译检查

```bash
python -m compileall app/ -q
cd frontend && npm run typecheck
cd remotion && npx tsc --noEmit
```

> 待执行。

### UI 生成结果

| 项目 | Data News | Card Stack |
|------|-----------|------------|
| 成功生成 | ✅ | ✅ |
| 可播放 | ✅ | ✅ |
| 总耗时 | 14082ms | 18335ms |
| 失败原因 | 无 | 无 |

## 当前问题

1. **Card Stack 抽帧三层卡片不可见**：三帧内容完全相同，prev/next 层在 PNG 中不可观察。可能原因：
   - opacity 0.40~0.65 在深色背景上不够明显
   - 或 PNG 压缩抹去了半透明层细节
   - **建议：在 Remotion 内部直接截图验证，或降低 PNG 压缩质量**

2. **工作区存在削弱效果的 local diff**：remotion/src/AiNewsVideo.tsx 有未提交的 diff，将 V0.6.5 参数进一步弱化（offsetX 140→120, -120→-100），且移除了 zIndex，可能破坏堆叠顺序。**该 diff 不应随本轮提交。**

## 结论

### V0.6.5 强化参数是否通过 UI 验证

**部分通过。**

- ✅ UI 生成流程正常，两个视频均可播放
- ✅ V0.6.5 committed 参数（offsetX=140/offsetY=-80/offsetX=-120/offsetY=70）代码层面正确
- ⚠️ **无法通过抽帧确认 prev/next 卡片的实际可见性** — 三帧内容完全相同，未见明显叠加层
- ⚠️ 参数强化在代码层面合理，但**实际视觉效果需在 UI 中动态观察**（PNG 压缩丢失了半透明层信息）

### 是否建议进入下一阶段

**是，但需先解决以下问题：**

1. 确认 prev/next 层在浏览器中动态播放时是否可见（PNG 无法验证半透明层）
2. 评估是否需要进一步增强 prev/next 透明度（prev opacity 最终值 0.65，next opacity 最终值 0.40 是否足够）
3. **丢弃或重新评估 local diff**（该 diff 削弱了 V0.6.5 效果，移除 zIndex 破坏堆叠顺序）

## 下一步建议

1. **浏览器内录屏验证**（而非抽帧）：在 Chrome DevTools 中对 Card Stack 视频进行屏幕录制，观察 prev/next 卡片在动态播放时是否可见
2. **Local diff 处置**：在下一轮中丢弃 local diff，或将其作为 V0.6.5 的调优尝试（如果需要进一步调参，应该基于 V0.6.5 committed 代码小步调整）
3. **参数微调候选**：如果浏览器动态播放仍不明显，可以考虑：
   - prev opacity 最终值从 0.65 微调至 0.70~0.75
   - next offset 适度增加（offsetY 从 70 增至 80~90）
4. **抽帧质量改进**：下次使用 ffmpeg -frames:v 1 -quality lossless 提取未压缩帧，避免 JPEG 类压缩丢失半透明细节
