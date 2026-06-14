# HyperFrames HTML Render Route — V0.3.2

## 概述

V0.3.2 新增第三条候选技术路线：**hyperframes_html_render**。

目标：验证 HyperFrames（HeyGen 插件能力）是否适合 AI 资讯共享视频。

> **当前状态：manual（手动路线）**
>
> 本轮不接真实 API，而是生成 HTML artifact，人工复制到 HyperFrames 插件中渲染。
> 如果视觉验证通过，未来再升级为 real route。

---

## 核心思路

```
同一份 AI 资讯内容
  → 生成 9:16 HTML 动态页面（单文件，无外部依赖）
  → 交给 HeyGen HyperFrames 插件渲染
  → 人工下载/记录结果
  → 回填 Route Benchmark 或记录为 external artifact
```

---

## 路线状态

| 状态 | 值 |
|------|-----|
| `route_id` | `hyperframes_html_render` |
| `status` | `manual` |
| `engine` | `hyperframes-html` |
| `resolution` | `1080x1920` (9:16 竖屏) |

---

## 技术实现

### 文件结构

```
app/video_lab/
  adapters/
    hyperframes_html_render.py   # 5-step adapter
  renderers/
    hyperframes/
      __init__.py
      html_builder.py             # HTML 生成器

tests/
  test_hyperframes_route.py      # 12 个测试（V0.3.2.1 新增 2 个）

docs/
  HYPERFRAMES_ROUTE_V0.3.2.md    # 本文档
```

### HTML 生成器（html_builder.py）

**输入：**

- `experiment_id`: 实验标识
- `structured`: 结构化内容（lead, subtitle）
- `key_points`: 关键点列表
- `params`: 渲染参数

**输出：**

- `runtime/video_lab/experiments/<experiment_id>/hyperframes/index.html`

**HTML 特性：**

- 竖屏 9:16，1080x1920 视觉比例
- 深色 AI 资讯风格（`#0a0e1a` 背景 + `#3b82f6` 强调色）
- Cover / KeyPoint / Summary 三类页面
- CSS keyframe animations（pageIn, fadeIn, slideUp）
- 自动轮播（每页 5 秒）
- 导航 dots
- 所有内容内联，单文件，无外部网络依赖
- 文字可读性优先，大字号

### Adapter（hyperframes_html_render.py）

**5 步流水线：**

1. **Receive Input** — 解析原始输入
2. **Structure Content** — 内容结构化
3. **Extract Key Points** — 提取关键点
4. **Build HTML Page** — 生成 HTML artifact
5. **Generate Conclusion** — 写入 manifest

**返回值：**

```python
VideoExperimentResult(
    videoUrl="",       # 无真实视频
    status="manual",
    assets={
        "method": "hyperframes_html_render",
        "engine": "hyperframes-html",
        "htmlUrl": "...",
        "routeMode": "manual",
        "requires": "HeyGen HyperFrames plugin",
    },
    rawOutput={
        "routeMode": "manual",
        "requires": "HeyGen HyperFrames plugin",
        "nextAction": "Paste HTML into HeyGen HyperFrames and render video",
    }
)
```

---

## 人工验收流程

1. 打开 `/video-lab/route-benchmark`
2. 选择测试用例（`case_ai_frontier_daily_001`）
3. 选择路线：`hyperframes_html_render`
4. 运行 benchmark
5. 打开生成的 HTML 链接
6. 复制 HTML 源码
7. 在 HeyGen HyperFrames 插件中粘贴
8. 设置输出参数（9:16, MP4）
9. 渲染视频
10. 下载视频，记录评分
11. 填入 Route Benchmark 评分面板

---

## 视觉质量评估维度

| 维度 | 评估标准 |
|------|---------|
| 是否可渲染 | HyperFrames 能否成功处理该 HTML |
| 9:16 控制 | 输出是否为竖屏视频 |
| MP4 输出 | 能否输出标准 MP4 格式 |
| 文字清晰度 | 中文是否清晰无锯齿 |
| 动效质量 | CSS 动画是否流畅自然 |
| vs Remotion | 是否优于 Remotion 方案 |

---

## 与其他路线的对比

| 维度 | local_frame_compose | template_programmatic_render | hyperframes_html_render |
|------|---------------------|------------------------------|-------------------------|
| 状态 | real | real | **manual** |
| 技术 | Pillow + FFmpeg | Remotion + React | **HTML + CSS + HyperFrames** |
| 文字控制 | 高 | 高 | **高（CSS 完全可控）** |
| 动效 | 弱（FFmpeg fade） | 中（React timing） | **强（CSS keyframes）** |
| 自动化 | ✅ 全自动 | ✅ 全自动 | ❌ 需人工复制粘贴 |
| 产品化 | ✅ 高 | ✅ 高 | ⚠️ 待验证 |

---

## 未来升级路径

如果本轮人工验证通过，可考虑：

1. **semi_auto**：保留 HTML 生成，接入 HyperFrames API 半自动渲染
2. **real**：完整 API 集成，全自动流水线

关键依赖：HeyGen HyperFrames API 开放程度。

---

## V0.3.2.1 — 收口

### 修复内容

1. **RouteScorePanel 支持 manual route 评分**
   - `scoreableStatuses = ["succeeded", "manual"]`
   - manual route 现在可以像 real route 一样被评分

2. **消除 manual route 误导性 warning**
   - `_build_warnings()` 对 `status == "manual_completed"` 返回 `[]`
   - 不再显示 "render status: manual_completed" 误导性提示

3. **RouteResultCard 说明更清晰**
   - 显示紫色说明文字："该路线已生成 HTML → 手动用 HyperFrames 渲染后再评分"
   - 操作步骤：打开 HTML → 复制源码 → 粘贴到插件 → 渲染视频

4. **测试覆盖**
   - `test_route_benchmark_runs_hyperframes_route`: 验证无 warnings
   - `test_build_warnings_empty_for_manual_completed`: 验证 `_build_warnings` 逻辑

### 人工验收状态

> **注意**：HeyGen HyperFrames 是 HeyGen 官方浏览器插件，需要在 HeyGen 应用内使用。本地开发环境无法直接调用 HyperFrames API 进行真实渲染。

route 代码已验证：
- ✅ HTML 生成正确（单文件、无外部依赖）
- ✅ Benchmark 可运行，不报错
- ✅ status 正确返回 `manual`
- ✅ 无误导性 warning
- ✅ 评分面板可见 manual route

人工验收待完成：
- ⬜ 在 HeyGen 中粘贴 HTML 并渲染视频
- ⬜ 记录视觉质量评分
- ⬜ 和 Remotion/local_frame 对比结论

---

## 相关文档

- [ROUTE_BENCHMARK_V0.3.md](ROUTE_BENCHMARK_V0.3.md)
- [VIDEO_CAPABILITY_LAB_ROADMAP.md](VIDEO_CAPABILITY_LAB_ROADMAP.md)
- [CHANGELOG.md](CHANGELOG.md)
