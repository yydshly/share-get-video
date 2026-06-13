# Video Capability Lab 架构文档

## 1. 核心数据流

```
VideoTestCase
    ↓
VideoExperimentInput (testCaseId + methodId + inputPayload)
    ↓
ExperimentRunner
    ↓
MethodRegistry → VideoMethodAdapter
    ↓
ProductionSteps[] (each with logs + keyData + artifacts)
    ↓
VideoExperimentResult
    ↓
VideoEvaluation (manual or system)
    ↓
VideoMethodAdvice
```

## 2. 核心对象关系

### VideoTestCase
定义标准测试场景（输入类型、目标时长、画面比例、验证重点）。
不包含运行时数据，只包含配置。

### VideoMethod
定义一种视频生成技术路线（6 类）。
包含 category、costLevel、controlLevel、stabilityLevel、productizationLevel。

### VideoExperiment
一次实验任务，包含输入、执行参数、状态、耗时。
通过 MethodRegistry 找到对应 Adapter 执行。

### VideoExperimentResult
一次实验的输出结果，包含 videoUrl、coverUrl、assets、logs。
核心是 ProductionSteps[] 和 Artifacts[]。

### VideoEvaluation
人工或系统评分（11 个维度各 1-5 分）。

### VideoMethodAdvice
根据场景输出的结构化建议，包含推荐方案、备选方案、不推荐方案、推理过程、技术栈建议、风险提示。

## 3. 核心模块职责

### testCaseRegistry (seed_data.py)
- 存储内置测试用例配置
- 提供 get_test_case_by_id / get_method_by_id 等查询函数
- 不做运行时决策

### methodRegistry (method_registry.py)
- 维护 MethodCategory → AdapterFunction 的映射
- ExperimentRunner 通过它找到正确的 Adapter
- Adapter 独立实现，不耦合 Runner

### ExperimentRunner
- 创建实验（create_experiment）
- 执行实验（run_experiment）
- 查询实验（get_experiment / list_experiments）
- 不包含业务逻辑，只负责调度

### VideoMethodAdapter (adapters/)
每个 MethodCategory 对应一个独立 Adapter：
- `local_frame_compose` → 本地帧合成
- `local_media_compose` → 本地素材合成
- `template_programmatic_render` → Remotion 模板
- `ai_video_direct` → AI 直接生成
- `ai_asset_then_compose` → AI 素材+合成
- `hybrid_pipeline` → 混合编排

每个 Adapter 接收 (experiment_id, input_payload, params)，返回 VideoExperimentResult。

### Planner 模块 (planners/)
- `content_structurer` - 将原始输入转为结构化内容
- `key_point_extractor` - 提取关键信息点
- `script_planner` - 生成视频脚本
- `storyboard_planner` - 生成分镜
- `asset_planner` - 生成素材计划（图片、音频、BGM）
- `render_planner` - 生成渲染参数计划

Planner 独立于 Adapter，可被不同 Adapter 复用。

### Advisor
- 根据 testCaseId 返回 VideoMethodAdvice
- 静态规则，不依赖运行时数据
- 独立于 UI 和 Runner

## 4. ProductionSteps 数据结构

每个实验执行后包含多个步骤：

```python
class VideoProductionStep:
    id: str
    name: str
    description: str
    status: VideoProductionStepStatus  # pending/running/succeeded/failed/skipped
    startedAt: datetime | None
    finishedAt: datetime | None
    elapsedMs: int | None
    inputSummary: str | None
    outputSummary: str | None
    keyData: dict | None
    logs: list[str]
    artifacts: list[VideoProductionArtifact]
```

每个步骤产出 Artifacts：

```python
class VideoProductionArtifact:
    id: str
    type: ArtifactType
    title: str
    summary: str
    payload: dict
```

## 5. UI 职责边界

UI（React 组件）只做：
- 数据展示
- 用户交互（表单、按钮）
- 路由跳转

UI **不做**：
- 业务逻辑判断
- Adapter 选择
- 实验执行
- 数据转换

所有业务逻辑在后端或 domain 层（planners/）。

## 6. 扩展点

### 接入真实 Pillow/FFmpeg
→ 实现 `local_frame_compose` adapter，在 `run_local_frame_compose()` 中调用真实库

### 接入真实 Remotion
→ 实现 `template_programmatic_render` adapter，在 `run_remotion_template()` 中调用 Node.js 子进程

### 接入真实视频模型
→ 实现 `ai_video_direct` adapter，在 `run_ai_video_direct()` 中调用 API

### 接入 TTS / 图像生成
→ 在 planners/ 中新增 tts_planner / image_gen_planner
→ 在 adapter 中调用

### 新增测试用例
→ 在 seed_data.py 的 SEED_TEST_CASES 中添加 VideoTestCase 实例
→ 在 advisor.py 的 ADVISOR_RULES 中添加推荐规则

### 新增技术路线
→ 在 models.py 的 MethodCategory 中添加新枚举值
→ 在 adapters/ 中添加新 adapter 文件
→ 在 method_registry.py 中注册
