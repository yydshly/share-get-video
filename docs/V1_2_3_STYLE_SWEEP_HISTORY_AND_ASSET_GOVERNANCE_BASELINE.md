# V1.2.3 Style Sweep 历史记录与运行资产治理基线

## 1. 阶段结论

Style Sweep 历史记录与运行资产治理 dry-run 基线已通过验收。

当前治理闭环：

1. 用户可以删除 Style Sweep 历史记录
2. 删除历史记录只删除 job JSON
3. 删除历史记录不删除视频 / 音频 / 字幕 / manifest / 图片资产
4. 后端可以扫描运行资产
5. 扫描结果区分 protected / deletable / skipped
6. Style Gallery sample 引用资产会被保护
7. 前端可以查看扫描结果
8. **当前没有真实资产删除能力**（仅 dry-run 扫描 + job JSON 删除）

---

## 2. 基线信息

| 项目 | 值 |
|------|-----|
| 分支 | `feature/v1.2.3-style-gallery-validation-center` |
| 验收页面 | `/video-lab/style-sweep` |
| 关联策略文档 | [V1.2.3 Style Sweep 运行资产清理策略](V1_2_3_STYLE_SWEEP_ASSET_CLEANUP_POLICY.md) |
| 关联闭环 1 | [V1.2.3 Style Sweep 验证中心基础闭环冻结记录](V1_2_3_STYLE_SWEEP_VALIDATION_BASELINE.md) |
| 关联闭环 2 | [V1.2.3 Style Sweep 到 Style Gallery 样片库沉淀闭环冻结记录](V1_2_3_STYLE_SWEEP_TO_GALLERY_BASELINE.md) |

### 关键提交

| commit | 说明 |
|--------|------|
| `d34aea9` | feat(style-sweep): delete sweep job records（后端删除 job JSON 接口） |
| `4f3f2fb` | feat(style-sweep): add history delete action（前端"删除记录"入口） |
| `b098847` | docs(style-sweep): define asset cleanup policy（清理策略文档） |
| `0619071` | feat(style-sweep): add asset cleanup dry-run scan（dry-run 扫描接口） |
| `5ee0eb8` | fix(style-sweep): align asset scan path normalization（路径保护修复） |
| `fca94c4` | feat(style-sweep): show asset scan preview（前端扫描结果展示） |

---

## 3. 已完成能力

### 3.1 历史记录删除

接口：

```http
DELETE /video-lab/style-sweep-jobs/{job_id}
```

| 行为 | 说明 |
|------|------|
| 删除对象 | `runtime/video_lab/style_sweep/jobs/{job_id}.json` |
| 视频 / 音频 / 字幕 / manifest / 图片 | 不删除 |
| job 不存在 | 返回 404 |
| 前端入口 | 历史记录列表中每条 job 后跟"删除记录"按钮（带 confirm 弹窗） |
| 删除当前打开 job | 清空 `data` / `jobId` / `issueMarks` / `promoteStates` 等当前结果状态 |
| 提示文案 | 删除成功后显示"✅ 已删除记录，视频资产未删除" |

> 当前任务只删 job JSON，绝不删任何运行资产。

### 3.2 资产清理策略

策略文档：[V1.2.3 Style Sweep 运行资产清理策略](V1_2_3_STYLE_SWEEP_ASSET_CLEANUP_POLICY.md)

核心原则：

```text
以 Style Gallery sample 为准。
只要 sample 引用某个文件，该文件就不能删除。
job JSON 删除，不等于资产可以删除。
```

策略文档明确定义：

- 资产分类（job JSON / 视频 / 音频 / 字幕 / manifest / 封面图 / AI 素材 / Remotion 中间产物）
- 受保护的引用字段集合（`sample.output.*` / `sample.asset_meta.*` / `sample.job_run.asset_refs.*`）
- 可清理资产的 4 个前提条件（无引用 / 非 running / job JSON 已删或全部失败 / 修改时间 > minAgeDays）
- 7 类危险场景（D-1 ~ D-7）
- 三档清理策略（保守 / 宽松 / 激进）

### 3.3 dry-run 扫描接口

接口：

```http
GET /video-lab/style-sweep-assets/scan
```

参数：

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `minAgeDays` | int | 7 | 早于该天数的未被引用文件才视为可清理候选 |
| `includeProtected` | bool | true | 是否把受保护资产也返回 |
| `limit` | int | 500 | 各类明细列表的最大返回条数 |

返回结构：

```json
{
  "dryRun": true,
  "root": "runtime/video_lab",
  "minAgeDays": 7,
  "totalAssetFiles": 120,
  "protectedCount": 40,
  "deletableCount": 80,
  "skippedCount": 0,
  "estimatedDeletableBytes": 123456789,
  "protectedItems": [
    {
      "path": "runtime/video_lab/experiments/.../final.mp4",
      "sizeBytes": 12345678,
      "reason": "referenced_by_style_gallery",
      "sampleIds": ["sample_xxx"]
    }
  ],
  "deletableItems": [
    {
      "path": "runtime/video_lab/experiments/.../final.mp4",
      "sizeBytes": 12345678,
      "lastModified": "2026-06-01T10:00:00Z",
      "reason": "unreferenced_older_than_min_age"
    }
  ],
  "skippedItems": [
    {
      "path": "runtime/video_lab/experiments/.../final.mp4",
      "sizeBytes": 12345678,
      "lastModified": "2026-06-15T10:00:00Z",
      "reason": "unreferenced_but_too_new"
    }
  ],
  "warnings": []
}
```

| 字段 | 说明 |
|------|------|
| `dryRun` | 恒为 `true`，接口只扫描不删 |
| `totalAssetFiles` | 扫描到的全部资产文件数（不含 `style_sweep/jobs/` 下的 job JSON） |
| `protectedCount` | 仍被 Style Gallery sample 引用的资产数 |
| `deletableCount` | 满足可清理条件（无引用 + 超过 minAgeDays）的资产数 |
| `skippedCount` | 无引用但太新、暂不清理的资产数 |
| `estimatedDeletableBytes` | 可清理候选累计字节数 |
| `warnings` | 扫描过程中产生的非致命警告（例如根目录不存在） |

### 3.4 protected 判断规则

`collect_referenced_assets()` 收集所有 Style Gallery sample 引用的资产路径：

- `sample.output.path` / `poster` / `audio_url` / `srt_url` / `manifest_url`
- `sample.asset_meta.*` 中所有 url 字段
- `sample.job_run.asset_refs.*` 中所有 url 字段

`normalize_asset_ref()` 把以下格式统一成 `runtime/video_lab/...` / `runtime/style_gallery/...`：

- `runtime/video_lab/...`（无前缀）
- `https://host/runtime/video_lab/...`（带域名）
- `D:\...\runtime\video_lab\...` / `D:/.../runtime/video_lab/...`（Windows 绝对路径）
- `/absolute/path/to/runtime/video_lab/...`（Linux 绝对路径）
- 空字符串 / `None` → `""`

扫描内部匹配路径统一为 `runtime/video_lab/...`，API 返回的 `path` 字段也统一为 `runtime/video_lab/...`，保证双向比对稳定。

#### 5ee0eb8 路径保护修复

提交 `5ee0eb8`（fix(style-sweep): align asset scan path normalization）修复了路径格式不一致导致的误判问题：

- 修复前：扫描内部使用 `video_lab/...`、sample 引用使用 `runtime/video_lab/...`，导致 referenced_assets 集合与扫描结果比对失败，已被 Style Gallery 引用但格式不一致的资产会被错误地归入 `deletableItems`。
- 修复后：`normalize_asset_ref()` 在引用收集与文件遍历两侧统一输出 `runtime/...` 前缀，扫描结果与 sample 引用严格匹配，受保护资产不再被误判为可清理。

### 3.5 前端展示

入口：`/video-lab/style-sweep`

新增区域：紧邻"最近 Sweep 记录"下方的「🧹 运行资产扫描 / 清理预览」面板（黄色边框突出 dry-run 性质）。

展示项：

1. dry-run 安全提示（明示"不会删除任何文件 / 候选只是候选 / Style Gallery 引用的资产会被保护"）
2. 最小存在天数输入（`minAgeDays`）
3. "🔍 扫描资产"按钮
4. 总资产文件数（`totalAssetFiles`）
5. 受保护资产数（`protectedCount`）
6. 可清理候选数（`deletableCount`）
7. 暂时跳过数（`skippedCount`）
8. 预计可释放空间（`estimatedDeletableBytes` 经 `formatBytes` 格式化）
9. 受保护明细（`protectedItems`，`<details>` 折叠，含 path / size / sampleIds / reason）
10. 可清理候选明细（`deletableItems`，`<details>` 折叠，含 path / size / lastModified / reason）
11. 暂时跳过的明细（`skippedItems`，`<details>` 折叠，含 path / size / lastModified / reason）

**前端没有真实删除按钮**。整个面板只有一个 "🔍 扫描资产" 按钮，仅触发 dry-run 扫描。

---

## 4. 测试结果

| 阶段 | 命令 | 结果 |
|------|------|------|
| 3A-1 | `pytest tests/test_style_sweep_jobs.py` | 16 passed |
| 3A-4 | `pytest tests/test_style_sweep_asset_scan.py` | 27 passed |
| 3A-4 | `pytest tests/test_style_sweep_jobs.py tests/test_style_gallery_store_datetime.py`（含 promotion / datetime） | 35 passed |
| 3A-4-FIX | `pytest tests/test_style_sweep_asset_scan.py` | 28 passed |
| 3A-4-FIX | `pytest tests/test_style_sweep_jobs.py tests/test_style_gallery_store_datetime.py` | 22 passed |
| 3A-4B | `npm run build` | passed（tsc + vite build，0 错误） |
| 3A-4B | `pytest tests/test_style_sweep_asset_scan.py` | 28 passed |

> 上述数字为各阶段交付时本地执行的实测结果；任何后续 re-run 数字若偏差 ±1-2 属正常。

---

## 5. 当前阶段不包含

明确以下事项不在当前阶段：

1. 不提供真实资产删除接口（cleanup endpoint）
2. 不提供真实资产删除按钮（前端）
3. 不删除任何 `mp4` / `mp3` / `wav` / `srt` / `ass` / `json` / `png` / `jpg` / `webp` 文件
4. 不移动任何文件
5. 不做定时清理
6. 不做批量 cleanup
7. 不清理 Style Gallery sample
8. 不清理 promoted sample 资产
9. 不修改 promote 逻辑
10. 不修改字幕逻辑
11. 不修改 Remotion
12. 不修改 TTS
13. 不修改 FFmpeg

---

## 6. 已知风险

1. **当前只提供 dry-run，不释放空间** — 资产仍持续累积，需要后续真实删除能力
2. **`limit=100` 时前端明细可能截断** — 当前 UI 一次最多展示 100 条各类明细，超出部分会从后端截断，需要再扫才能看全
3. **外部手动复制 runtime 链接无法被系统追踪** — 用户复制到外部笔记 / 分享给别人的资产无法被 referenced_assets 覆盖
4. **真实删除前必须重新扫描 `referenced_assets`** — 防止扫描后到删除之间的窗口期有新 promote 写入引用
5. **真实删除必须默认 `dryRun=true`** — 接口契约必须如此
6. **真实删除必须 `confirm=true`** — 必须显式二次确认才执行
7. **真实删除最好先移动到 cleanup backup 目录** — 而非直接 `rm`，便于人工兜底

---

## 7. 下一阶段建议

### 推荐：阶段 3A-5A — 安全资产删除接口设计稿 / API contract

**原因**：当前已具备 dry-run 扫描 + job JSON 删除能力，但 runtime 资产仍在持续累积。直接进入实现风险高，先用一份 design doc 把以下问题定下来再做：

- cleanup endpoint 契约（路径、参数、错误码）
- 三档策略（保守 / 宽松 / 激进）的默认行为
- cleanup backup 目录格式与保留期
- 并发安全（删除期间新 promote 写入的引用）
- 操作审计日志
- 前端双确认 UI（dry-run 弹窗 → 二次确认 → 进度展示）

### 备选：阶段 3B — Remotion 模板差异化与背景丰富度审计

**原因**：Style Sweep 三路线中 Remotion 路线完成度最高（14 样式），但部分样式背景较为单薄，可作为后续优化方向。

> 如果继续资产治理，下一步先写 3A-5A 真实删除接口设计，不直接实现删除。

---

## 8. 相关文档

- [V1.2.3 Style Sweep 验证中心基础闭环冻结记录](V1_2_3_STYLE_SWEEP_VALIDATION_BASELINE.md)
- [V1.2.3 Style Sweep 到 Style Gallery 样片库沉淀闭环冻结记录](V1_2_3_STYLE_SWEEP_TO_GALLERY_BASELINE.md)
- [V1.2.3 Style Sweep 运行资产清理策略](V1_2_3_STYLE_SWEEP_ASSET_CLEANUP_POLICY.md)
