# Route Playground — V0.3.4

## 概述

V0.3.4 新增「视频生成链路测试台」页面，让用户不需要理解复杂参数，也能用固定样例分别跑每条技术路线并查看结果。

---

## 页面路径

```
/video-lab/route-playground
```

入口：首页导航卡片「链路测试台」🎬

---

## 核心交互

### 1. 测试样例区

页面顶部固定展示测试样例（AI 前沿日报），用户可直接编辑，支持重置为默认内容。

### 2. 路线选择区

每条路线以卡片形式展示，包含：
- 路线名称
- 状态标签（real / manual / mock / reserved）
- 一句话说明
- 运行条件
- 预计产物

用户通过勾选选择要测试的路线。

默认选中：
- `local_frame_compose` ✅
- `template_programmatic_render` ✅
- `hyperframes_html_render` ✅

`tts_subtitle_compose` 默认不选中，旁边有费用警告提示。

### 3. 运行按钮

- **运行已选路线**：执行选中的路线
- **恢复默认选择**：重置为默认勾选

### 4. 结果展示

每条路线运行后展示结果卡：

**succeeded**：
- 视频播放器（videoUrl）
- 🔊 播放音频（audioUrl）
- 📝 打开字幕（srtUrl）
- 📋 manifest 链接

**manual**：
- 🎬 打开 HTML
- 操作说明：复制 → 粘贴到 HeyGen HyperFrames → 渲染

**failed**：
- 明确显示失败原因（warnings）
- 不隐藏错误信息

### 5. 评分系统

每条成功或 manual 的路线支持 8 维度评分：

| 维度 | 说明 |
|------|------|
| 信息准确性 | 内容是否准确 |
| 文字可读性 | 字幕/文字是否清晰 |
| 视觉质量 | 画面美观度 |
| 动态表现 | 动效流畅度 |
| 生成稳定性 | 批量生成一致性 |
| 自动化程度 | 需要多少人工干预 |
| 成本可控性 | 成本是否可控 |
| 产品化潜力 | 产品化价值 |

支持填写「一句话结论」。

评分保存在前端 state，不入库。

### 6. Markdown 导出

点击「导出 Markdown 对比报告」生成包含以下内容的报告：

- 测试输入
- 参与路线
- 每条路线的生成状态 + videoUrl + 评分
- 横向评分表
- 当前判断（最佳路线、暂缓路线等）
- 下一步建议

---

## 技术实现

**前端**：`RoutePlaygroundPage.tsx`

**后端**：复用现有 Route Benchmark API，不新增 endpoint
- `POST /video-lab/route-benchmarks` — 创建并运行 benchmark
- `GET /video-lab/routes` — 获取路线列表

**状态管理**：前端 state + localStorage（评分）

---

## 与 Route Benchmark 页面的区别

| 维度 | Route Benchmark | Route Playground |
|------|----------------|-----------------|
| 目标用户 | 开发者/高级用户 | 快速验证者 |
| 样例输入 | 需手动填写 | 默认样例，可直接运行 |
| 路线选择 | 复选框 | 卡片勾选 |
| TTS 警告 | 无 | 有明确费用提示 |
| 评分 | 分散在 RouteScorePanel | 集中展示 |
| 导出报告 | 无 | Markdown 一键导出 |
| HyperFrames 操作说明 | 基础 | 详细步骤提示 |

---

## 相关文档

- [ROUTE_BENCHMARK_V0.3.md](ROUTE_BENCHMARK_V0.3.md)
- [TTS_SUBTITLE_ROUTE_V0.3.3.md](TTS_SUBTITLE_ROUTE_V0.3.3.md)
- [HYPERFRAMES_ROUTE_V0.3.2.md](HYPERFRAMES_ROUTE_V0.3.2.md)
