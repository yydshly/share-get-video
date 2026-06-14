# V0.2.5 / V0.2.5.1 样例验收文档

## 概述

V0.2.5 将 `local_frame_compose` 从固定模板能力升级为可配置、可复验、可验收的 AI 资讯分享视频模板。

> V0.2.5.1 修复了参数真实接入问题：keyPointCount 截断不再伪造数量、includeOverview/includeSummary 正确接入、1:1 分辨率正确映射、warning 消息显示原始非法值。

---

## 一、样例生成命令

### 前置条件

1. **启动后端服务**
   ```bash
   cd d:/claude_code/20260607_ai实现获取前沿知识/share-get-video
   uvicorn app.main:app --reload --port 8000
   ```

2. **安装 FFmpeg**（必需）
   - Windows: `winget install ffmpeg` 或 `choco install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

### 运行样例脚本

```bash
cd d:/claude_code/20260607_ai实现获取前沿知识/share-get-video
python scripts/generate_ai_frontier_sample.py
```

### 通过 UI 运行

1. 打开前端：`http://localhost:5173`（或 `vite` 启动的地址）
2. 进入「创建实验」页面
3. 选择测试用例：`case_ai_frontier_daily_001`（今日 AI 前沿共享短视频）
4. 选择生成方案：`method_local_frame_compose`（本地图像帧合成）
5. 填写标题，如 `AI资讯样例-V0.2.5`
6. 在「生成参数」面板中填入推荐参数（见第二节）
7. 点击「Run Experiment」

---

## 二、推荐参数

V0.2.5 推荐参数固化如下：

```json
{
  "targetDuration": 45,
  "aspectRatio": "9:16",
  "keyPointCount": 6,
  "highlightMode": "auto",
  "transitionEnabled": true,
  "transitionFrames": 4,
  "stylePreset": "ai_frontier_dark"
}
```

| 参数 | 值 | 说明 |
|------|-----|------|
| targetDuration | 45 | 目标时长 45 秒 |
| aspectRatio | 9:16 | 竖屏格式，适合朋友圈/社媒 |
| keyPointCount | 6 | 关键点数 6 个 |
| highlightMode | auto | 自动提取数字、百分比、倍数等高亮词 |
| transitionEnabled | true | 启用 fade 转场 |
| transitionFrames | 4 | 每组转场 4 帧中间帧 |
| stylePreset | ai_frontier_dark | AI Frontier Dark 视觉风格 |

---

## 三、验收维度

人工评分维度：

| 维度 | 说明 | 5分（优秀）| 3分（一般）| 1分（差）|
|------|------|------------|------------|----------|
| 信息准确性 | 内容转译是否准确 | 完全准确 | 基本准确 | 有错误 |
| 可读性 | 字幕/文字是否清晰易读 | 非常清晰 | 基本可读 | 难以阅读 |
| 视觉质量 | 画面美观程度 | 专业精美 | 中规中矩 | 简陋粗糙 |
| 节奏感 | 视频节奏是否舒适 | 节奏恰当 | 基本合理 | 过快/过慢 |
| 传播吸引力 | 封面和内容是否吸引分享 | 很有吸引力 | 一般 | 没有吸引力 |

---

## 四、人工评分表

实验完成后，在详情页底部「人工评分」区域评分：

```
信息准确性：_/5
可读性：_/5
视觉质量：_/5
节奏感：_/5
传播吸引力：_/5
稳定性：_/5（生成一致性）
产品化价值：_/5

备注：
```

---

## 五、当前样例结果记录方式

实验完成后记录：

1. **experiment_id**：实验 ID
2. **videoUrl**：生成的 MP4 地址
3. **coverUrl**：封面图片地址
4. **manifestUrl**：manifest.json 地址
5. **人工评分**：各维度得分和备注

记录位置：实验详情页 URL，可直接分享

---

## 六、runtime 产物说明

**重要：不提交 runtime/ 产物到 Git**

运行时生成的文件：

- `runtime/experiments/{experiment_id}/output.mp4` - 生成的视频
- `runtime/experiments/{experiment_id}/frames/*.png` - 生成的帧图片
- `runtime/experiments/{experiment_id}/manifest.json` - 实验清单

这些文件：
- 仅保存在本地 `runtime/` 目录
- 不应提交到 Git 仓库
- 服务重启后会保留（除非手动清理）

---

## 七、根据评分调参

### 如果 visualQuality <= 3

建议调整：
- 优化封面/背景/字号/卡片层次
- 后续版本迭代视觉风格

### 如果 readability <= 3

建议调整：
- 减少 `keyPointCount`（如从 6 降到 4）
- 或增加 `targetDuration`（如从 45 增到 60）

### 如果 pacing <= 3

建议调整：
- 调整 `targetDuration`（增减 10-15 秒）
- 调整 `transitionFrames`（从 4 减到 2 或增到 6）

### 如果 shareability <= 3

建议调整：
- 优化封面标题
- 增强 CTA（Call-to-Action）
- 后续版本增加片尾模板

---

## 八、模板验收结论规则

系统自动根据评分给出模板状态：

| 状态 | 条件 | 含义 |
|------|------|------|
| usable | 平均分 >= 4 | 可作为默认模板 |
| needs_tuning | 2.5 <= 平均分 < 4 | 需要调参后重新验证 |
| not_ready | 平均分 < 2.5 | 不建议作为模板 |

---

## 九、下一轮调参方法

V0.2.6 预期工作：

1. 运行真实样例（使用推荐参数）
2. 人工给分
3. 根据评分调整：
   - `targetDuration` ±10-15
   - `keyPointCount` ±2
   - `transitionFrames` 2/4/6 对比
   - `highlightMode` auto/numbers/none 对比
4. 固化默认推荐参数
5. 决定是否进入 V0.3 Remotion 方案评估

---

## 十、待人工评分

> ⚠️ 截至 V0.2.5 发布，以下样例尚未完成人工评分：
>
> ```
> experiment_id: 待生成后记录
> videoUrl: 待生成后记录
> manifestUrl: 待生成后记录
> ```
>
> **请先运行样例脚本完成真实生成，再进行人工评分。**

---

## 十一、快速参考

### 参数校验规则

| 参数 | 范围 | 默认 | 超出处理 |
|------|------|------|----------|
| targetDuration | 15-90 | 45 | 自动 clamp |
| keyPointCount | 1-10 | 6 | 自动 clamp |
| transitionFrames | 0-8 | 4 | 自动 clamp |
| highlightMode | auto/numbers/none | auto | fallback 到 auto |
| stylePreset | ai_frontier_dark | ai_frontier_dark | fallback 到默认 |

### 关键文件

- 脚本：`scripts/generate_ai_frontier_sample.py`
- 参数模型：`app/video_lab/renderers/render_params.py`
- 适配器：`app/video_lab/adapters/local_frame_compose.py`
- 渲染器：`app/video_lab/renderers/local_frame_renderer.py`
