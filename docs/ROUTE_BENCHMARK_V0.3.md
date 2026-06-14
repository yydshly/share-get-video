# ROUTE_BENCHMARK_V0.3.md

## 概述

V0.3.0 新增多路线横向验证框架（Route Benchmark）。

目标：**同一份 AI 资讯内容 → 多条技术路线 → 统一展示 → 统一评分 → 判断哪条路线值得继续深入**。

---

## 核心概念

### Route（技术路线）

一条完整的视频生成技术路线，包含：

- `routeId`: 唯一标识
- `name`: 路线名称
- `status`: 实现状态
- `description`: 路线描述
- `expectedPipeline`: 预期处理步骤列表

### 路线状态

| 状态 | 说明 | 是否真实执行 |
|------|------|-------------|
| `real` | 已有真实 adapter，可产出真实视频 | ✅ 是 |
| `mock` | 占位实现，未接入真实 API | ❌ 否 |
| `reserved` | 预留路线，等待未来实现 | ❌ 否 |

---

## 已注册路线

| routeId | 名称 | 状态 | 说明 |
|---------|------|------|------|
| `local_frame_compose` | 本地图像帧合成 | **real** | Pillow + FFmpeg |
| `template_programmatic_render` | Remotion 程序化渲染 | mock | 需 Node.js + Remotion CLI |
| `tts_subtitle_compose` | TTS + 字幕合成 | mock | 需 TTS API |
| `ai_asset_then_compose` | AI 素材 + 本地合成 | mock | 需 LLM/TTS/图像 API |
| `ai_video_direct` | 大模型直接生成视频 | reserved | 视频模型 API 未接入 |
| `hybrid_pipeline` | 混合编排流水线 | reserved | 需完整路由引擎 |

---

## API

### GET /video-lab/routes

获取所有已注册路线列表。

```bash
curl http://localhost:8000/video-lab/routes
```

响应示例：

```json
[
  {
    "routeId": "local_frame_compose",
    "name": "本地图像帧合成",
    "status": "real",
    "description": "使用 Pillow 生成信息卡片帧，FFmpeg 合成视频...",
    "expectedPipeline": ["接收输入", "结构化内容", ...]
  },
  ...
]
```

### POST /video-lab/route-benchmarks

创建并执行多路线横向验证。

```bash
curl -X POST http://localhost:8000/video-lab/route-benchmarks \
  -H "Content-Type: application/json" \
  -d '{
    "testCaseId": "case_ai_frontier_daily_001",
    "title": "AI资讯多路线对比",
    "inputPayload": {"content": "今日AI前沿..."},
    "commonParams": {
      "targetDuration": 45,
      "keyPointCount": 6,
      "highlightMode": "auto",
      "transitionEnabled": true,
      "transitionFrames": 4,
      "stylePreset": "ai_frontier_dark"
    },
    "routeIds": ["local_frame_compose", "template_programmatic_render", "ai_video_direct"]
  }'
```

### GET /video-lab/route-benchmarks/{benchmark_id}

获取指定 benchmark 结果。

---

## 前端页面

路径：`/video-lab/route-benchmark`

入口：首页导航「多路线验证」

功能：
1. 选择测试用例（自动填入 defaultInput）
2. 多选技术路线
3. 设置公共参数（commonParams）
4. 点击运行 benchmark
5. 展示每条路线结果卡片
   - `real` 路线：展示真实 video
   - `mock` 路线：展示 expectedPipeline 和 warnings
   - `reserved` 路线：展示路线说明和评估

---

## RouteScorePanel

前端评分组件，对真实路线进行多维度评分：

| 维度 | 说明 |
|------|------|
| 信息表达清楚度 | 内容是否清晰易读 |
| 视觉质量 | 画面美观程度 |
| 节奏感 | 视频节奏是否舒适 |
| 分享价值 | 是否有传播吸引力 |
| 稳定性 | 批量生成一致性 |
| 实现复杂度 | 技术实现难度 |
| 产品化潜力 | 产品化价值 |
| 值得继续深挖 | 综合判断 |

> 注意：当前评分仅存在前端 state，不要求后端持久化。

---

## 数据模型

### RouteResult

```typescript
interface RouteResult {
  routeId: string;
  status: "succeeded" | "failed" | "mock" | "reserved";
  videoUrl: string;
  coverUrl: string;
  manifestUrl: string;
  summary: string;
  artifacts: unknown[];
  metrics: {
    generationTimeMs: number;
    estimatedCost: string;
    stability: string;
    qualityCeiling: string;
  };
  warnings: string[];
}
```

### RouteBenchmark

```typescript
interface RouteBenchmark {
  benchmarkId: string;
  title: string;
  testCaseId: string;
  inputPayload: Record<string, unknown>;
  commonParams: Record<string, unknown>;
  routeIds: string[];
  status: "pending" | "running" | "completed" | "partial";
  results: RouteResult[];
  createdAt: string | null;
  completedAt: string | null;
  elapsedMs: number | null;
}
```

---

## 相关文件

- `app/video_lab/routes_benchmark/models.py` - 数据模型
- `app/video_lab/routes_benchmark/registry.py` - 路线注册表
- `app/video_lab/routes_benchmark/runner.py` - Benchmark 执行器
- `app/video_lab/router.py` - API 路由（新增 `/routes`, `/route-benchmarks`）
- `frontend/src/video-lab/pages/RouteBenchmarkPage.tsx` - Benchmark 页面
- `frontend/src/video-lab/components/RouteScorePanel.tsx` - 评分面板
- `tests/test_route_benchmark.py` - API 测试

---

## V0.3.1 预期

Remotion 最小真实路线验证：同一份 case_ai_frontier_daily_001 → Remotion 模板 → MP4 → 回填 Route Benchmark → 和 local_frame_compose 横向对比。
