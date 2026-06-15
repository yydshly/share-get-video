# V0.7.0 视频生成实验台主线报告

## 分支与 Commit

- 分支：`feature/v0.3.6-b1-shotplan-standardization`
- 最新 commit：待提交

## 背景

V0.5.x / V0.6.x 验证了多条视频路线（Remotion、Pillow、AI素材）和 Remotion 子范式（Data News、Card Stack），但项目陷入局部动画细节，缺乏统一的主线工作台让用户在 UI 中完成端到端流程。

核心原则：**所有关键能力必须 UI 可见，人必须在回路中观察结果、确认结果、决定下一步。**

## 为什么回到主线

1. 局部优化（Card Stack 叠层）缺少用户反馈验证
2. 各路线分散在多个页面，没有统一入口
3. 没有"人在回路"机制——用户无法人工确认生成结果
4. 缺少从内容输入到生成到确认的完整流程

## 本轮目标

新增 `/video-lab/workbench` 页面，让用户完成：

```
输入内容 → 选择路线 → 生成预览 → 观看结果 → 人工确认 → 保存/对比/复制
```

## 修改文件

1. `frontend/src/video-lab/pages/VideoGenerationWorkbenchPage.tsx` — **新增**，主线工作台页面
2. `frontend/src/video-lab/pages/VideoLabHome.tsx` — 新增"视频生成实验台"入口卡片
3. `frontend/src/App.tsx` — 添加 `/video-lab/workbench` 路由
4. `docs/OPEN_ISSUES_VIDEO_LAB.md` — **新增**，开放问题记录
5. `docs/VIDEO_GENERATION_WORKBENCH_V0.7.0.md` — **新增**，本轮报告

## UI 入口

```
http://localhost:5173/video-lab/workbench
```

首页 Video Lab 可通过「视频生成实验台」卡片进入。

## 页面结构

### 1. 内容输入区

- 标题输入框（预填充示例：今日 AI 前沿速递）
- 正文 textarea（预填充三条 AI 新闻，逗号/空行分隔要点）
- "加载示例内容"按钮

### 2. 路线选择区

| 路线 | 状态 | 说明 |
|------|------|------|
| Pillow 信息卡片 | ✅ 可生成 | 静态卡 + Ken Burns 动效，秒级 |
| Remotion Data News | ✅ 可生成 | 数字滚动+数据条，数据驱动型 |
| Remotion Card Stack | ✅ 可生成 | 卡片堆叠短视频感，V0.6.5.2 强化 |
| AI 素材氛围 | ⚠️ 暂未接入 | AI 生图+叠卡，成本高，下阶段 |

### 3. 生成控制区

- "生成预览"按钮 → 调用 `POST /clip-preview`
- "生成完整视频"按钮 → 占位，标注"下一阶段接入"
- loading 状态显示当前路线和预计耗时
- 错误信息展示

### 4. 结果观看区

生成成功后展示：

- `<video controls>` 播放器
- experiment_id
- videoUrl / runtimePath
- elapsedMs
- 路线名称

失败时展示 failed_reason + 重试提示。

### 5. 人工观察确认区

状态类型：`pending | approved | problem | discarded`

| 状态 | 触发 | 显示动作 |
|------|------|---------|
| pending | 生成成功后默认 | 三个确认按钮 |
| approved | 用户点击"通过" | 保存样片 / 加入对比 / 复制路径 |
| problem | 用户点击"有问题" | 重新生成 / 记录问题 |
| discarded | 用户点击"丢弃" | 丢弃说明 |

观察备注 textarea 始终可用。

## 已接入路线

| 路线 | 是否可生成预览 | 是否 UI 可见 | 当前限制 |
|------|--------------|-------------|---------|
| Pillow 信息卡片 | ✅ 是 | ✅ 是 | 无 |
| Remotion Data News | ✅ 是 | ✅ 是 | 无 |
| Remotion Card Stack | ✅ 是 | ✅ 是 | V0.6.5.2 prev/next 可见性已修复 |
| AI 素材氛围 | ❌ 否 | ❌ 否 | 标记为 preview_only，暂未接入 |

## 人在回路设计

```
生成 → 用户观看视频 → 用户判断：
  ├── 通过 → 保存样片 / 加入对比 / 复制路径
  ├── 有问题 → 记录问题 / 重新生成
  └── 丢弃 → 不保存
```

核心原则：**不自动保存，不自动升级模板，人工确认后才允许后续操作。**

## 遗留问题记录

详见 `docs/OPEN_ISSUES_VIDEO_LAB.md`：

1. ✅ Card Stack 图层可见性（V0.6.5.2 已修复）
2. ✅ Local diff 清理（已处理）
3. ✅ 测试文件不存在（确认非问题）
4. ⚠️ style-family/compare 为连续生成，非并行
5. ⏳ Card Stack 价值评估（待用户反馈）
6. ⚠️ AI 素材路线预览未完整接入
7. ⏳ Remotion LLM 内容规划未做
8. ⏳ 完整视频生成未接入

## 测试结果

| 检查项 | 结果 |
|--------|------|
| `python -m compileall app/` | ✅ 通过 |
| `npm run typecheck` (frontend) | ✅ 通过 |
| `npx tsc --noEmit` (remotion) | ✅ 通过 |

> 无新增后端接口，无 pytest 测试文件。

## 当前问题

1. **AI 素材路线未接入**：标记为 `preview_only`，用户选择后提示"暂未接入预览"
2. **完整视频未接入**：工作台只有 preview，完整视频（TTS+字幕+合成）下一阶段接入
3. **保存/对比功能为占位**：approved 后三个按钮均 alert "下一阶段接入"
4. **Card Stack 验证期标识保留**：PREV/NEXT 角标是验证期临时方案

## 结论

### 主线是否重新打通

**是。** V0.7.0 建立了统一工作台：

- ✅ `/video-lab/workbench` 页面已创建
- ✅ 首页能进入该页面（VideoLabHome 卡片）
- ✅ 用户能输入内容（标题+正文+示例加载）
- ✅ 用户能选择路线（4 条路线，含 experimental/stable/preview_only 状态）
- ✅ 用户能点击生成预览（调用 `/clip-preview`）
- ✅ UI 能显示视频结果或失败原因
- ✅ 用户能人工标记：通过/有问题/丢弃
- ✅ 只有人工通过后才显示保存/对比/复制路径动作
- ✅ 遗留问题有文档记录
- ✅ 不提交 runtime 产物
- ✅ 测试通过

### 是否建议进入下一阶段

**是。** V0.7.0 工作台已建立主线路径，下一阶段建议：

1. 接入 AI 素材路线完整预览（或明确标记为不可用）
2. 接入完整视频生成链路（TTS+字幕+合成）
3. 将保存/对比/复制路径从 alert 占位升级为实际功能
4. 基于用户反馈决定 Card Stack 是否值得继续投入

## 下一步建议

### 短期（下一迭代）

1. **完整视频生成**：接入 TTS + 字幕合成，实现真正的端到端出片
2. **AI 素材路线**：评估是否接入或明确放弃
3. **保存样片功能**：对接 style-samples 或新建简化样片存储

### 中期

1. **多路线并行生成**：工作台支持同时生成多条路线对比
2. **对比收藏夹**：保存 approved 视频进入对比集合
3. **Card Stack 用户反馈**：收集工作台用户对 Card Stack 的主观评价

### 长期

1. **用户账号与历史**：工作台结果持久化
2. **自动评分辅助**：人工确认时展示 auto quality score 作为参考
3. **模板系统升级**：基于人工确认结果自动学习用户偏好
