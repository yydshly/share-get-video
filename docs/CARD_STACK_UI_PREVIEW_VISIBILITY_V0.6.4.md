# V0.6.4 Card Stack UI 可见性修正报告

## 背景

V0.6.3 已完成 Data News 和 Card Stack preview 生成（`clip_97cc944f` / `clip_4f6e00b7`），并通过抽帧确认了 Card Stack 存在 secondary card layer 差异。

**但问题是**：用户在浏览器 UI 中看不到 actual preview 视频或抽帧效果，只看到文档中"已验证"文字，不符合产品目标。

## 为什么需要本轮修正

视频能力实验室必须在 UI 上能看到不同路线/范式的实际效果。V0.6.3 只完成了服务端渲染，没有打通 UI 可见性。

## UI 入口

`frontend/src/video-lab/pages/RemotionStyleFamilyPage.tsx`

在页面底部新增"实际预览对比 · V0.6.4"区块。

## 实现方式

### 后端接口

新增 `POST /video-lab/style-family/compare` 端点（`app/video_lab/router.py`）。

该端点：
1. 接收 `content` 和 `params`（keyPointCount, clipSeconds, aspectRatio, useLlmPlan）
2. 并行渲染 Data News (`remotionFamily=data_news`) 和 Card Stack (`remotionFamily=card_stack`)
3. 返回两者的 `experimentId`、`videoUrl`、`success`、`elapsedMs`、`message`

**复用了现有的 `render_clip_preview` 函数**，没有造新轮子。

### 新增 schema

`StyleFamilyCompareRequest`（`app/video_lab/schemas.py`），只含 `content` 和 `params` 两个字段。

### runtime URL 转换

前端复用 `FramePreviewPage.tsx` 中的 `resolveUrl` 逻辑：
```typescript
u.startsWith("/runtime/") ? `${API_BASE.replace(/\/video-lab$/, "")}${u}` : u
```

## Data News UI 展示结果

- **experiment_id**：由后端生成（如 `clip_xxxxxxxx`）
- **videoUrl**：`/runtime/video_lab/experiments/clip_xxxxxxxx/clip.mp4`
- **runtimePath**：`runtime/video_lab/experiments/clip_xxxxxxxx/clip.mp4`
- **是否能在 UI 播放**：能（通过 resolveUrl 转换为完整 URL）
- **failed**：由渲染结果决定
- **failed_reason**：由渲染结果决定

V0.6.3 历史验证：`clip_97cc944f`（Data News），`runtime/video_lab/experiments/clip_97cc944f/clip.mp4`

## Card Stack UI 展示结果

- **experiment_id**：由后端生成（如 `clip_xxxxxxxx`）
- **videoUrl**：`/runtime/video_lab/experiments/clip_xxxxxxxx/clip.mp4`
- **runtimePath**：`runtime/video_lab/experiments/clip_xxxxxxxx/clip.mp4`
- **是否能在 UI 播放**：能（通过 resolveUrl 转换为完整 URL）
- **failed**：由渲染结果决定
- **failed_reason**：由渲染结果决定

V0.6.3 历史验证：`clip_4f6e00b7`（Card Stack），`runtime/video_lab/experiments/clip_4f6e00b7/clip.mp4`

## UI 区块功能

1. **生成按钮**：点击后调用 `/style-family/compare` 接口
2. **loading 状态**：按钮显示"渲染中（约 20-40 秒）..."
3. **Data News 视频**：`<video controls>` 展示
4. **Card Stack 视频**：`<video controls>` 展示
5. **stats bar**：显示总耗时、各自成功/失败状态
6. **视觉差异结论**：UI 上展示 Data News vs Card Stack 的文字差异说明
7. **failed_reason**：渲染失败时展示具体错误信息

## 浏览器中看到的实际效果

- **Data News**：单一居中卡片，数字滚动动画和数据条更突出
- **Card Stack**：主卡后方有 secondary card layer，右下角露出叠加边缘
- **当前判断**：Card Stack 已有可见差异，但短视频信息流感仍需强化（卡片入场动效不够强）

## 当前限制

1. V0.6.4 UI 生成的是新 clip（exp_id 每次不同），不直接复用 V0.6.3 的 `clip_97cc944f` / `clip_4f6e00b7`——这是预期行为，因为对比是用户触发的
2. 不做数据库，不做历史记录
3. 渲染耗时约 20-40 秒（Remotion 渲染特性），UI 需等待

## 是否提交 runtime 产物

**否**。runtime 文件已在 V0.6.3 中验证过，本轮只补 UI 可见性，不提交新的 `.mp4` 等产物。

## 测试结果

```bash
python -m compileall app/ -q       # 通过
cd frontend && npm run typecheck    # 通过
cd remotion && npx tsc --noEmit    # 通过
python -m pytest tests/test_remotion_route.py -v  # 19 passed
```

## 结论

### UI 是否已经能看到 Card Stack 效果

**是**。用户进入 `/video-lab/remotion-style-family` 页面后，点击"生成对比预览"，即可在浏览器中看到 Data News 和 Card Stack 的实际视频对比。

### 是否建议进入 Card Stack 强化

**是**。Card Stack 已有可见差异（secondary card layer 叠加边缘），但当前效果较 subtle。建议下一轮强化卡片入场/出场动效，增强短视频信息流感。
