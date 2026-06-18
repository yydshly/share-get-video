# V1.2.3 Remotion Visual Technique Expansion

## 1. 背景

V1.2.4 阶段先把 `academic_sketch`（暖纸手绘风）落地，V1.2.5 阶段又把 `blueprint`（深蓝晒图风）加入。
两个 technique 形成了一条稳定的最小实现链路：

```text
效果样机库中的方向
→ 转成 visualTechnique
→ props_builder 透传参数
→ style_family_service 白名单允许
→ Remotion data.ts 类型扩展
→ AiNewsVideo.tsx 中 BackgroundLayer / surface 样式实现
→ Visual Technique Matrix 中真实生成视频
```

本次 V1.2.5+ 任务沿用同一套链路，把效果样机库剩余 3 个核心方向也接入真实可渲染的 `visualTechnique`，
使 Visual Technique Matrix 一次性可以横向比较 5 个技法方向。

## 2. 当前已实现的 5 个 visualTechnique

| ID | 来源 | 视觉定位 |
|---|---|---|
| `academic_sketch` | V1.2.4 / academic | 暖米纸 + 网格 + 手绘批注（暖纸冷墨） |
| `blueprint` | V1.2.5 / blueprint | 深蓝晒图 + 白色工程网格 + 角标记（冷调） |
| `data_viz_dashboard` | V1.2.5+ / dataviz | 深色数据看板 + 动态柱/折线/圆环 + 漂浮指标 chip |
| `agent_sandbox_25d` | V1.2.5+ / sandbox | 2.5D 等距空间 + Agent 节点 + 数据包 + violet/cyan |
| `kinetic_code_typography` | V1.2.5+ / typography | IDE 编辑器 + 伪代码语法高亮 + 终端日志 + cursor 闪烁 |

## 3. 与效果样机库（Effect Prototype Gallery）的对应关系

| Prototype (RemotionLabPage) | visualTechnique | implementationLevel |
|---|---|---|
| `academic_sketch` | `academic_sketch` | `implemented_minimal` |
| `blueprint` | `blueprint` | `implemented_minimal` |
| `data_viz_dashboard` | `data_viz_dashboard` | `implemented_minimal`（本次升级） |
| `agent_sandbox_25d` | `agent_sandbox_25d` | `implemented_minimal`（本次升级） |
| `kinetic_code_typography` | `kinetic_code_typography` | `implemented_minimal`（本次升级） |

注意：本次仅把 prototype 从 `prototype_reference` 升级为 `implemented_minimal`。
**没有**把它们标记为 `visually_accepted`，**没有**接入 Style Sweep，**没有**接入 Style Gallery。

## 4. Visual Technique Matrix 默认改为 1×5

V1.2.4 阶段默认请求是 `3 families × 1 technique = 3 clips`。
如果继续用 3 families × 5 techniques = 15，会超过 `MAX_MATRIX_ITEMS = 9`。

本次把默认请求改为：

```json
{
  "matrix": {
    "families": ["data_news"],
    "visualTechniques": [
      "academic_sketch",
      "blueprint",
      "data_viz_dashboard",
      "agent_sandbox_25d",
      "kinetic_code_typography"
    ]
  }
}
```

UI 文案同步改为：

```text
1 family × 5 visual techniques = 5 clips
当前矩阵用于横向比较 5 种 visualTechnique。这些 technique 来自 Effect Prototype Gallery。
这里生成的是 lab-only 样片，不写 Style Sweep，不写 Style Gallery。
```

为什么不用 3×5：

- 后端 `MAX_MATRIX_ITEMS = 9` 仍然保留。
- 横向比较 5 个 technique 的视觉差异，只需要固定 1 个 family，避免 family 自身带来的版面变化。
- 用户仍可在 UI 中手动改为 2×4 / 1×9 等组合（只要 ≤ 9）。

## 5. 各 Technique 视觉实现要点

### 5.1 data_viz_dashboard

- 背景：深色 `#070d1a` + radial 蓝紫光晕
- 装饰：
  - 8 根 frame-driven 动画柱状图（cyan→purple 渐变 + glow）
  - frame-driven 折线图（polyline + data points）
  - 双层圆环（外圈 cyan / 内圈 violet，frame 驱动 stroke-dasharray 动画）
- 漂浮 metric chip：3 个（98.7% / +24.3K / QPS 12.4k），frame 驱动轻微上下浮动
- surface：dark glass card + cyan border + 浅蓝字

### 5.2 agent_sandbox_25d

- 背景：深紫 `#0c0820` + radial violet/cyan 光晕
- 等距网格：`perspective(800px) rotateX(48deg)` 透视
- 5 个 Agent 节点：planner / model / tool / memory / user
  - 圆形 + radial gradient + 节点中心 highlight dot
  - frame 驱动上下浮动
- 5 条节点间通讯线路（虚线）
- 5 个发光数据包：frame 沿 edge 推进
- surface：violet glass + 浅紫字 + 紫色 title shadow

### 5.3 kinetic_code_typography

- 背景：IDE 暗色 `#0d1117` + 微弱 radial gradient
- 右上：editor panel
  - 顶部 macOS 三色圆点 + 文件名 `agent.ts`
  - 6 行伪代码（function / const / for / yield ...）
  - syntax highlight：keyword 红 / string 蓝 / function 紫 / 普通 白
  - 闪烁 cursor（frame/12 步进）
- 左下：terminal panel
  - 4 行 log（绿色 ok / 黄色 warn）
  - `$ run` 行 + 闪烁 cursor
- 角落小标签 `KINETIC_CODE_TYPOGRAPHY · v0.1`
- surface：editor dark + green/cyan border + 浅绿字

## 6. 改动文件清单

| 文件 | 改动 |
|---|---|
| `remotion/src/data.ts` | `VisualTechnique` 类型扩展到 5 项 |
| `remotion/src/AiNewsVideo.tsx` | 新增 3 个 `BackgroundLayer` 分支；`getTechniqueSurface` 新增 3 套 surface |
| `app/video_lab/renderers/remotion/props_builder.py` | `visualTechnique` 透传白名单扩展到 5 项 |
| `app/video_lab/services/style_family_service.py` | `VALID_VISUAL_TECHNIQUES` 扩展到 5 项；更新 docstring |
| `frontend/src/video-lab/pages/RemotionLabPage.tsx` | 3 个 prototype 从 `prototype_reference` 升级为 `implemented_minimal` |
| `frontend/src/video-lab/pages/RemotionStyleFamilyPage.tsx` | 默认矩阵改为 1×5；UI 文案更新为 V1.2.5 |
| `tests/test_style_family_visual_technique_matrix.py` | 新增 6 个测试覆盖 5 technique / 1×5 / 3×5 over-limit / invalid |

## 7. 显式不做的事情

本次任务 **没有** 触碰：

- Style Sweep
- Style Gallery / Style Gallery promote
- Recipe System
- 任意第 6 个 `visualTechnique`
- 任意 D3 / Recharts / Three.js / Canvas 新依赖
- 把任意 technique 标记为 `visually_accepted`
- 删改 `academic_sketch` / `blueprint` 既有实现
- 主链路生成逻辑（`render_clip_preview` / `props_builder` 主流程）

## 8. 验收结果

### 8.1 单元测试

```text
pytest tests/test_style_family_visual_technique_matrix.py   →  13/13 passed
pytest tests/test_remotion_style_resolution.py              →  26/26 passed
```

### 8.2 接口实测（1 family × 5 techniques = 5 clips）

```bash
curl -X POST http://127.0.0.1:8777/video-lab/style-family/visual-technique-matrix \
  -H "Content-Type: application/json" \
  -d '{
    "content": "AI 系统正在从单模型问答走向多智能体协作，评估重点也从答案正确转向过程可解释、工具调用和系统稳定性。",
    "params": {"clipSeconds": 2, "keyPointCount": 2},
    "matrix": {
      "families": ["data_news"],
      "visualTechniques": [
        "academic_sketch",
        "blueprint",
        "data_viz_dashboard",
        "agent_sandbox_25d",
        "kinetic_code_typography"
      ]
    }
  }'
```

预期：

```text
HTTP 200
items.length = 5
success = 5/5
5 个 videoUrl 均存在
```

边界用例：

- `3 families × 5 techniques = 15` → HTTP 400，提示 visual technique matrix is limited to 9 clips
- 未知 technique → HTTP 400，提示 visualTechniques filter resulted in empty set

## 9. 当前结论

| 维度 | 状态 |
|---|---|
| 工程实现 | ✅ 完成 |
| 接口测试 | ✅ 完成（pytest + live API） |
| `npm run build` | ✅ 通过 |
| 浏览器人工视觉验收 | ⏳ 待人工执行（每个 technique 风格不同，需要分别观察） |

5 个 `visualTechnique` 已经具备在 Visual Technique Matrix 中横向比较样片的工程条件。
视觉层面仍需人工打开 `/video-lab/remotion-style-family` 确认每种 technique 的氛围是否符合预期。
本次**不**为视觉验收背书，**不**把它们标记为 `visually_accepted`。
