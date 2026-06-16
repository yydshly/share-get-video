# V1.1.0 Video Lab Product Main Flow Freeze

## 1. 版本定位

Video Lab V1.1.0 是视频生成能力实验室的主流程冻结版本。

它不是最终产品，也不是 AI 新闻短视频 MVP，而是：

- 视频生成路线验证实验台
- 样片资产沉淀工具
- rerun payload 复现参数工具
- compare bundle 对比决策工具

## 2. 产品主目标

```
输入一段 AI 新闻 / 产品动态 / 技术摘要
→ 在 Workbench 中选择路线
→ 生成 preview / full video
→ 观察 JobRun 状态
→ 人工判断结果
→ 保存样片
→ 在 Style Gallery 查看资产
→ 复制 rerun payload
→ 加入对比
→ 保存 Compare Bundle
→ 得出路线/参数决策
```

## 3. V1 主流程页面

### 3.1 Video Lab 首页

**路径：** `/video-lab`

**职责：**
- 展示 Video Lab 定位
- 提供主工作台入口
- 提供样片库入口
- 提供高级实验区入口

### 3.2 Workbench

**路径：** `/video-lab/workbench`

**职责：**
- 输入内容
- 选择生成路线
- 生成 preview
- 生成 full video
- 展示 JobRun
- 保存 approved / rejected 样片

### 3.3 Style Gallery

**路径：** `/video-lab/style-gallery`

**职责：**
- 查看样片资产
- 查看实验资产信息
- 复制 rerun payload
- 加入/移除对比
- 保存 Compare Bundle
- 查看历史 Compare Bundle
- 删除 Compare Bundle

### 3.4 Compare Panel

**位置：** Style Gallery 内 compare tab

**职责：**
- 展示 comparing 样片
- 按 visual_judgement.score 排序
- 展示无评分提示
- 保存当前对比包

## 4. 高级实验区页面

这些页面保留，但不属于 V1 主链路必经步骤：

| 路径 | 用途 |
|------|------|
| `/video-lab/style-sweep` | 风格批量对比 |
| `/video-lab/technique-probe` | 路线探测排名 |
| `/video-lab/remotion-style-family` | Remotion 范式对比 |
| `/video-lab/quality-history` | 质量历史记录 |
| `/video-lab/frame-preview` | 单帧预览 |
| `/video-lab/visual-compose` | 视觉合成 |
| `/video-lab/route-baseline-comparison` | 路线基线对比 |
| `/video-lab/experiments/new` | 新建实验 |
| `/video-lab/route-benchmark` | 路线基准测试 |
| `/video-lab/route-playground` | 路线探索场 |
| `/video-lab/compare` | 通用对比（已迁移到 Style Gallery） |
| `/video-lab/advice` | 路线推荐建议 |
| `/video-lab/methods` | 方法列表 |
| `/video-lab/test-cases` | 测试用例 |

## 5. 稳定 API Contract

### 5.1 Workbench / Generation

| 接口 | 方法 | 用途 |
|------|------|------|
| `/video-lab/clip-preview` | POST | 生成预览片段 |
| `/video-lab/visual-compose` | POST | 生成完整视频 |

**要求：**
- 成功/失败都应返回结构化结果
- 成功/失败都应尽量携带 jobRun
- 不应抛出无结构错误给前端

### 5.2 Style Sample

| 接口 | 方法 | 用途 |
|------|------|------|
| `/video-lab/style-samples` | GET | 列出样片 |
| `/video-lab/style-samples` | POST | 保存样片 |
| `/video-lab/style-samples/{sample_id}` | GET | 获取单个样片 |
| `/video-lab/style-samples/{sample_id}` | DELETE | 删除样片 |
| `/video-lab/style-samples/{sample_id}/rerun-payload` | GET | 获取复现参数 |
| `/video-lab/style-samples/{sample_id}/compare` | POST | 标记为对比中 |
| `/video-lab/style-samples/{sample_id}/status` | POST | 更新状态 |
| `/video-lab/style-samples/{sample_id}/judge` | POST | 视觉评分 |

### 5.3 Compare Bundle

| 接口 | 方法 | 用途 |
|------|------|------|
| `/video-lab/style-compare-bundles` | POST | 创建对比包 |
| `/video-lab/style-compare-bundles` | GET | 列出对比包 |
| `/video-lab/style-compare-bundles/{bundle_id}` | GET | 获取单个对比包 |
| `/video-lab/style-compare-bundles/{bundle_id}` | DELETE | 删除对比包 |

## 6. 正式资产字段

### StyleSample V1 正式字段

| 字段 | 说明 |
|------|------|
| id | 样片唯一ID |
| route_id | 路线ID |
| route_name | 路线展示名 |
| style_name | 风格名称 |
| description | 风格描述 |
| status | 状态（candidate/approved/rejected/comparing） |
| params | 生成参数 |
| output | 输出文件信息 |
| evaluation | 人工评价 |
| tags | 标签列表 |
| content_preview | 内容摘要 |
| duration_sec | 视频时长 |
| audio_duration_sec | 音频时长 |
| created_at | 创建时间 |
| visual_judgement | AI 视觉评分（可选） |
| source | 来源元信息 |
| generation | 生成元信息 |
| asset_meta | 资产元信息 |
| quality_meta | 质量元信息 |
| review_meta | 审核元信息 |
| job_run | 任务运行信息 |
| schema_version | 模式版本 |

### V1.1.0 后正式依赖的关键字段

| 字段路径 | 用途 |
|----------|------|
| `params.fullContent` | rerun payload 内容来源 |
| `source.source_type` | 样片来源类型 |
| `source.experiment_id` | 实验ID |
| `source.run_id` | 运行ID |
| `source.job_id` | 任务ID |
| `generation.visual_route` | 视觉路线 |
| `generation.visual_profile` | 视觉配置 |
| `generation.aspect_ratio` | 宽高比 |
| `generation.target_duration` | 目标时长 |
| `asset_meta.final_video_url` | 视频地址 |
| `asset_meta.cover_url` | 封面地址 |
| `asset_meta.manifest_url` | 清单地址 |
| `quality_meta.structural_score` | 结构评分 |
| `review_meta.review_status` | 审核状态 |
| `job_run.status` | 任务状态 |
| `job_run.stage` | 任务阶段 |
| `schema_version` | 模式版本 |

## 7. Compare Bundle 正式字段

### CompareBundle

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 对比包唯一ID |
| title | string | 标题 |
| goal | string | 对比目标 |
| sample_ids | list[string] | 样片ID列表 |
| items | list[CompareBundleItem] | 样片详情列表 |
| decision | CompareBundleDecision | 决策信息 |
| tags | list[string] | 标签 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |
| schema_version | string | 模式版本（1.0.7） |

### CompareBundleItem

| 字段 | 类型 | 说明 |
|------|------|------|
| sample_id | string | 样片ID |
| route_id | string | 路线ID |
| route_name | string | 路线名称 |
| style_name | string | 风格名称 |
| status | string | 状态 |
| score | float/null | 视觉评分 |
| grade | string | 等级 |
| video_url | string | 视频地址 |
| poster_url | string | 封面地址 |
| manifest_url | string | 清单地址 |
| rerun_payload_available | bool | 是否可复现 |
| notes | string | 备注 |

### CompareBundleDecision

| 字段 | 类型 | 说明 |
|------|------|------|
| winner_sample_id | string | 胜出样片ID |
| winner_reason | string | 胜出原因 |
| rejected_sample_ids | list[string] | 淘汰样片ID列表 |
| rejected_reasons | dict | 淘汰原因映射 |
| productization_notes | string | 产品化备注 |

## 8. V1.1.0 不做的事情

以下能力**不**进入 V1.1.0：

| 类别 | 排除项 |
|------|--------|
| 用户系统 | 用户账号系统、多租户、计费 |
| 后端架构 | 云端任务队列、Redis/Celery、数据库迁移 |
| 生成能力 | 自动批量生成视频、自动选择最优路线、自动重跑失败样片 |
| 发布能力 | 自动发布抖音/小红书/B站、发布分享页 |
| 内容能力 | 复杂剪辑时间线、长视频生产、AI 新闻源抓取、新闻摘要 Agent |
| 运营能力 | 用户管理、权限控制、审核工作流 |

## 9. 已知问题 / Backlog

### P2（可修复，非阻塞）

| 编号 | 问题 | 建议版本 |
|------|------|----------|
| 1 | 前端 dev server 端口提示文案未根据实际端口更新 | V1.2.x |
| 2 | 真实 clipboard UI 体验仍需浏览器截图确认 | V1.2.x |
| 3 | full video 真实浏览器链路仍需人工持续观察 | V1.2.x |

### P3（非阻塞优化）

| 编号 | 问题 | 建议版本 |
|------|------|----------|
| 1 | 需要补充浏览器截图存入文档 | V1.2.x |
| 2 | Style Gallery 信息密度偏高 | V1.2.x |
| 3 | Compare Bundle 历史列表展示偏简略 | V1.2.x |
| 4 | 需要后续补 GitHub Actions CI | V1.2.x |
| 5 | 需要补更清晰的产品级空状态 | V1.2.x |

## 10. V1.1.0 验收边界

### 通过条件

- [x] API 层主流程闭环已验证
- [x] 自动化测试通过（717 passed）
- [x] 前端 typecheck/build 通过
- [x] Workbench / Style Gallery / Compare Bundle 主入口清晰
- [x] V1 主流程和高级实验区边界清晰
- [x] Contract 字段冻结
- [x] Backlog 明确

### 不要求

- 真实发布分享
- 用户系统
- 云端异步队列
- 所有视频路线视觉质量达到产品级
- 真实浏览器截图全部补齐

## 11. 下一阶段方向

V1.1.0 之后进入：

**V1.2.0 AI 新闻短视频 MVP**

V1.2.0 重点不再是通用视频实验室，而是聚焦一个具体产品场景：

```
AI 新闻 / 产品动态 / 技术摘要
→ 自动生成短视频方案
→ 用 V1.1.0 冻结的主流程验证路线
→ 输出可发布样片
```

## 12. 文档索引

| 文档 | 版本 | 用途 |
|------|------|------|
| V1.0.8 Main Flow Smoke Test | V1.0.8 | 主流程自动化 + API 验证 |
| V1.1.0 Product Main Flow Freeze | V1.1.0 | 主流程冻结 + 边界定义 |
