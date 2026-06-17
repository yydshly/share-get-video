# V1.2.3 Style Sweep 运行资产清理策略

> 本文档定义 Style Sweep 运行资产的分类、引用关系、以及后续安全清理必须遵守的规则。
> 当前阶段（3A-1 / 3A-2）仅实现删除 job JSON 记录，不删除任何运行资产。

---

## 1. Style Sweep 会产生哪些资产？

### 1.1 记录文件

| 类型 | 说明 |
|------|------|
| job JSON | `runtime/video_lab/style_sweep/jobs/{job_id}.json`，包含执行参数、结果、标注、进度 |

### 1.2 视频 / 音频 / 字幕文件

| 类型 | 字段来源 | 典型路径 |
|------|----------|----------|
| 最终视频 | `result.finalVideoUrl` / `result.videoUrl` | `runtime/video_lab/experiments/{id}/final.mp4` |
| 音频 | `result.audioUrl` | `runtime/video_lab/experiments/{id}/audio.mp3` |
| 字幕（SRT） | `result.srtUrl` | `runtime/video_lab/experiments/{id}/subs.srt` |
| 字幕（ASS） | `result.assUrl` | `runtime/video_lab/experiments/{id}/subs.ass` |
| Manifest | `result.manifestUrl` | `runtime/video_lab/experiments/{id}/manifest.json` |
| 封面图 | `result.coverUrl` | `runtime/video_lab/experiments/{id}/poster.jpg` |

### 1.3 中间 / 素材文件

| 类型 | 说明 |
|------|------|
| AI 素材图片 | AI 路线生成的 PNG/JPG 图片 |
| Remotion 中间产物 | Remotion 渲染过程中产生的临时文件 |
| Pillow 生成图片 | Pillow 路线生成的单帧图片 |
| 临时合成目录 | 合成过程中产生的中间帧目录 |

---

## 2. 资产可能被哪些地方引用？

### 2.1 Style Gallery sample（最关键）

当一个 Style Sweep result 被提升到 Style Gallery 后，sample 记录会保存这些引用：

```
sample.output.path               → finalVideoUrl
sample.output.poster             → coverUrl
sample.output.audio_url          → audioUrl
sample.output.srt_url           → srtUrl
sample.output.manifest_url       → manifestUrl
sample.asset_meta.final_video_url
sample.asset_meta.cover_url
sample.asset_meta.audio_url
sample.asset_meta.srt_url
sample.asset_meta.manifest_url
sample.job_run.asset_refs.video_url
sample.job_run.asset_refs.cover_url
sample.job_run.asset_refs.audio_url
sample.job_run.asset_refs.srt_url
sample.job_run.asset_refs.ass_url
sample.job_run.asset_refs.manifest_url
```

### 2.2 job JSON 内部引用

job JSON 本身记录了所有 result 中的 URL，这些 URL 指向具体文件。

### 2.3 外部引用（风险场景）

用户可能：
- 手动将 runtime 路径复制到外部笔记
- 将视频链接分享给其他人
- 复制文件到其他目录

这些外部引用无法在代码层追踪，但属于"一旦误删会造成问题"的场景。

---

## 3. 哪些资产绝对不能自动删除？

**核心原则：只要有 Style Gallery sample 引用，就不能删除。**

具体而言，以下文件禁止自动删除：

```text
1. sample.output.path 指向的 final video 文件
2. sample.output.poster 指向的 cover 文件
3. sample.output.audio_url 指向的音频文件
4. sample.output.srt_url 指向的 SRT 字幕文件
5. sample.output.manifest_url 指向的 manifest 文件
6. sample.asset_meta 中记录的任意资产路径
7. sample.job_run.asset_refs 中记录的任意资产路径
8. 任何 source.source_type = "style_sweep" 的 sample 关联文件
```

**特别说明**：即使 job JSON 被删除，只要 sample 存在，sample 引用的文件就必须保留。

---

## 4. 哪些资产可以安全删除？

满足以下**全部条件**的资产，可以考虑清理：

```text
1. 该文件未被任何 Style Gallery sample 引用（不在 referenced_assets 中）
2. 该文件不归属于当前正在运行的 job（running / pending 状态）
3. 该文件对应的 job JSON 已经被删除
   或者：该 job 对应的样式全部被判定为无效（如全部 failed）
4. 该文件修改时间距离现在超过 N 天（建议 7 天）
```

---

## 5. 如何判断一个 job 是否已经被提升到 Style Gallery？

当 job 中某个 styleId 被 promote 后：

1. Style Gallery 会创建一条 sample，记录 `source.source_type = "style_sweep"` 和 `source.job_id = job_id`
2. 同时记录 `source.run_id = styleId`
3. 因此可以通过以下方式判断：

```python
# 伪代码
def is_job_promoted(job_id: str) -> bool:
    samples = sg_store.list_samples(source_type="style_sweep")
    return any(s.source.job_id == job_id for s in samples)

def get_promoted_style_ids(job_id: str) -> set[str]:
    samples = sg_store.list_samples(source_type="style_sweep")
    return {
        s.source.run_id
        for s in samples
        if s.source.job_id == job_id
    }
```

**注意**：即使 job JSON 被删除，Style Gallery sample 仍然存在，所以 job JSON 删除不等于"这个 job 的资产可以删"。

---

## 6. 删除 job JSON 和删除资产的区别

| 操作 | 影响的文件 | 当前阶段是否实现 |
|------|-----------|----------------|
| 删除 job JSON | `runtime/video_lab/style_sweep/jobs/{job_id}.json` | ✅ 已实现 |
| 删除视频文件 | `finalVideoUrl` / `videoUrl` 指向的 mp4 | ❌ 不在本阶段 |
| 删除音频文件 | `audioUrl` 指向的 mp3 | ❌ 不在本阶段 |
| 删除字幕文件 | `srtUrl` / `assUrl` 指向的文件 | ❌ 不在本阶段 |
| 删除 manifest | `manifestUrl` 指向的 json | ❌ 不在本阶段 |
| 删除封面图 | `coverUrl` 指向的图片 | ❌ 不在本阶段 |

**job JSON 删除后，job 记录消失，但文件仍在。必须等所有 sample 都确认不再引用这些文件后，才能安全删除。**

---

## 7. referenced_assets 集合构建规则

后续清理逻辑必须先构建受保护文件集合：

```python
def collect_referenced_assets() -> set[str]:
    """收集所有 Style Gallery sample 引用的资产路径（已去重）。"""
    referenced = set()
    for sample in sg_store.list_samples(limit=10000):
        # output 字段
        for field in ("path", "poster", "audio_url", "srt_url", "manifest_url"):
            val = getattr(sample.output, field, None)
            if val:
                referenced.add(val)

        # asset_meta 字段
        for field in ("final_video_url", "cover_url", "audio_url", "srt_url", "manifest_url"):
            val = getattr(sample.asset_meta, field, None)
            if val:
                referenced.add(val)

        # job_run.asset_refs
        asset_refs = sample.job_run.get("asset_refs", {})
        for val in asset_refs.values():
            if val:
                referenced.add(val)

    return referenced
```

**所有在 referenced_assets 中的文件，绝对不能删除。**

---

## 8. 危险场景（必须避免）

### D-1：job JSON 被删除，但 sample 仍引用其视频资产

这是最常见的陷阱。job JSON 里记录的 URL 和 sample 引用的文件完全相同，删 JSON 时文件还在，但很多人会误以为"删了 JSON 就应该可以删文件"。

**正确做法**：以 Style Gallery sample 为准，不以 job JSON 为准。

### D-2：多个 sample 复用同一个视频文件

一个 finalVideoUrl 可能被多个 styleId 的 promote 共同引用。删除前必须确认没有任何 sample 引用它。

### D-3：手动复制链接到外部笔记

无法追踪，必须默认"文件可能有外部引用"，即不能依赖"没有任何 sample 引用"就认为可以删除。

### D-4：路径格式不统一

同一文件可能记录为：
- `runtime/video_lab/experiments/abc/final.mp4`
- `/runtime/video_lab/experiments/abc/final.mp4`
- `D:/runtime/video_lab/experiments/abc/final.mp4`（Windows 绝对路径）
- `https://cdn.example.com/runtime/video_lab/experiments/abc/final.mp4`

清理逻辑必须规范化路径后再比较。

### D-5：正在运行的 job 资产还没写完

running 状态的 job，其 output 还没完全写入。如果提前扫描，可能认为文件不存在而跳过，或误判为孤儿资产。

### D-6：旧样片 schema 中资产字段不完整

早期 sample 记录可能只有 `output.path`，没有 `asset_meta` 和 `job_run.asset_refs`。扫描时必须同时检查 output.path。

### D-7：Remotion 中间产物与最终产物混淆

Remotion 会产生大量中间帧文件，可能和 final mp4 存在同一目录下。清理时必须只删 final mp4 / audio / manifest，不要误删中间产物（除非能确认中间产物已被消费）。

---

## 9. 后续阶段规划

### 阶段 3A-4：资产扫描 dry-run 接口

**目标**：只扫描，不删除，返回可清理资产列表。

```http
GET /video-lab/style-sweep-assets/scan
```

返回结构：

```json
{
  "totalAssetFiles": 120,
  "protectedCount": 40,
  "deletableCount": 80,
  "estimatedDeletableBytes": 123456789,
  "deletableItems": [
    {
      "path": "runtime/video_lab/experiments/abc/final.mp4",
      "sizeBytes": 12345678,
      "jobId": "sweep_xxx",
      "lastModified": "2026-06-01T10:00:00Z",
      "reason": "orphan_unreferenced"
    }
  ],
  "protectedItems": [
    {
      "path": "runtime/video_lab/experiments/def/final.mp4",
      "reason": "referenced_by_sample",
      "sampleIds": ["sample_xxx"]
    }
  ]
}
```

### 阶段 3A-5：安全资产删除接口

**目标**：在 dry-run 确认后，真正删除孤立资产。

```http
POST /video-lab/style-sweep-assets/cleanup
```

请求体：

```json
{
  "dryRun": true,
  "paths": ["runtime/video_lab/experiments/abc/final.mp4"],
  "confirm": false
}
```

| 参数 | 说明 |
|------|------|
| `dryRun` | `true` 时只返回将删除的摘要，不实际删除 |
| `paths` | 要删除的文件路径列表（留空表示全部扫描到的可删除文件） |
| `confirm` | 必须 `true` 才真正删除；`false` 或不提供时默认 dryRun |

返回：

```json
{
  "dryRun": false,
  "requestedCount": 5,
  "deletedCount": 5,
  "skippedCount": 0,
  "protectedCount": 0,
  "deleted": [
    { "path": "runtime/...", "sizeBytes": 123456 }
  ],
  "skipped": [],
  "protected": [],
  "log": "Cleaned 5 files, skipped 0, estimated freed 123456 bytes"
}
```

**安全规则**：
- 必须跳过所有 referenced_Assets 中的文件
- 必须记录删除日志
- 建议创建删除备份快照（将文件移动到 `.cleanup_backup/{timestamp}/` 而非直接 rm）
- 删除操作建议在维护窗口执行，不要在高峰时段

---

## 10. 建议的清理策略

### 策略 A：最保守（推荐先用）

```text
只清理满足以下全部条件的文件：
1. 该文件不在 referenced_assets 中
2. 文件修改时间 > 30 天前
3. 对应 job 不在 running/pending 状态
4. 该 job JSON 已不存在（即已被删除）
```

### 策略 B：宽松清理

```text
只清理满足：
1. 不在 referenced_assets 中
2. 对应 job 已完成且无 running 状态
3. 文件修改时间 > 7 天前
```

### 策略 C：激进清理（高风险）

```text
跳过 referenced_assets，
按时间或大小阈值清理其余文件。

⚠️ 不推荐，可能误删外部引用文件。
```

---

## 11. 当前阶段不包含

| 禁止项 | 说明 |
|--------|------|
| ❌ 不实现资产扫描接口 | 留到 3A-4 |
| ❌ 不实现资产删除接口 | 留到 3A-5 |
| ❌ 不删除任何 mp4/mp3/srt/ass/json/png/jpg 文件 | 本阶段只删 JSON |
| ❌ 不修改 Style Sweep 页面 | 已在 3A-2 完成 |
| ❌ 不修改 Style Gallery 页面 | 无需修改 |
| ❌ 不改 promote 逻辑 | 无需修改 |
| ❌ 不改 job 删除接口 | 已有 |
| ❌ 不做定时清理 | 定时任务不在本阶段范围 |
| ❌ 不做批量删除 | 安全策略未确认前不允许 |

---

## 12. 相关文档

- [V1.2.3 Style Sweep 验证中心基础闭环冻结记录](V1_2_3_STYLE_SWEEP_VALIDATION_BASELINE.md)
- [V1.2.3 Style Sweep 到 Style Gallery 样片库沉淀闭环冻结记录](V1_2_3_STYLE_SWEEP_TO_GALLERY_BASELINE.md)
