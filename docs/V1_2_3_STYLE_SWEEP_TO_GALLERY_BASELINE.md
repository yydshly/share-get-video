# V1.2.3 Style Sweep 到 Style Gallery 样片库沉淀闭环冻结记录

## 1. 阶段结论

Style Sweep → Style Gallery 样片库沉淀闭环已通过验收。

该闭环已支持：
1. **从 Style Sweep 历史 job 中选择成功样式** — 页面支持对单个 succeeded result 触发提升
2. **不重新生成视频** — promote 接口纯复用已有资产，无任何 render 调用
3. **复用已有视频资产** — finalVideoUrl / audioUrl / srtUrl / assUrl / manifestUrl / coverUrl 完整保留
4. **创建 Style Gallery sample** — 通过 POST /style-sweep-jobs/{job_id}/promote 接口
5. **支持重复提升时复用已有 sample** — 幂等设计，reused=true 返回已有样片
6. **支持跳转到样片库查看** — 提升成功后显示"去样片库查看"链接
7. **样片库可正常加载并展示** — created_at naive/aware 混合排序问题已修复

---

## 2. 基线信息

| 项目 | 值 |
|------|-----|
| 分支 | feature/v1.2.3-style-gallery-validation-center |
| 后端 promote 基础 commit | 9e591a8307d4d9ddff99c578a6640f005b933fcd |
| promote 错误码修复 commit | d18fd88aa87e14b3d892769af88262aa482bffb9 |
| 前端提升入口 commit | feb34ae7403f3137185cbcb552ab4badd2792237 |
| 样片库排序修复 commit | 99de40c66654639f309906d90084e5dbc5cbcc0b |
| 验收页面 | /video-lab/style-sweep |
| 样片库验收 URL | /video-lab/style-gallery?tab=gallery&sample_id=\<sampleId\> |

---

## 3. 已完成能力

| # | 能力 | 说明 |
|---|------|------|
| 1 | POST /style-sweep-jobs/{job_id}/promote | 后端核心接口 |
| 2 | 只提升 succeeded result | status!=succeeded 进入 skipped |
| 3 | 不重新生成视频 | 纯资产复用，无 render 调用 |
| 4 | 保存 source=style_sweep | 样片来源标识 |
| 5 | 保存 sweepJobId / styleId | 来源 job 和样式标识 |
| 6 | 保存 routeId / routeName | 技术路线信息 |
| 7 | 保存 video_url / manifest_url / audio_url / srt_url / ass_url / cover_url | job_run.asset_refs 完整保留 |
| 8 | 保存 manualMark | 来自 job.manualMarks[styleId] |
| 9 | 保存 subtitleDiagnostics | 来自 rawOutput.subtitleDiagnostics |
| 10 | 重复 promote 幂等 | reused=true 返回已有 sample |
| 11 | 前端提升按钮 | 位于 Style Sweep 结果卡片 |
| 12 | 提升中 / 已提升 / 已在样片库状态显示 | PromoteState 状态机 |
| 13 | "去样片库查看"链接 | 带 sample_id 参数跳转 |
| 14 | created_at naive/aware 混合排序修复 | store.py + models.py |

---

## 4. 验收结果

### API 层

| 接口 | 结果 | 说明 |
|------|------|------|
| POST /style-sweep-jobs/{job_id}/promote | ✅ 通过 | promotedCount/samples 返回正确 |
| GET /video-lab/style-gallery/route-fit | ✅ 不再 500 | created_at 排序修复后正常 |
| GET /video-lab/style-gallery/samples | ✅ 通过 | list_samples 正常返回 |

### 前端层

| 验收项 | 结果 | 说明 |
|--------|------|------|
| 提升按钮显示条件 | ✅ 通过 | jobId 存在 + status=succeeded + 有 videoUrl |
| 无 jobId 时按钮置灰 | ✅ 通过 | title 提示"当前结果不是 job 模式" |
| 提升中状态 | ✅ 通过 | 显示"提升中..." |
| 成功后"已提升到样片库" | ✅ 通过 | 绿色显示 + 跳转链接 |
| reused=true 显示"已在样片库" | ✅ 通过 | 紫色显示 + 跳转链接 |
| skipped 时显示原因 | ✅ 通过 | 显示 reason 标签翻译 |
| 历史 job 打开后 promoteStates 清空 | ✅ 通过 | openHistoryJob 中 reset |

### 样片库层

| 验收项 | 结果 | 说明 |
|--------|------|------|
| /video-lab/style-gallery 不再 Failed to fetch | ✅ 通过 | created_at 排序修复 |
| promoted sample 可见 | ✅ 通过 | sample 正常写入 JSONL |
| 样片加入验证篮 | ⚠️ 待验收 | 不阻塞当前沉淀闭环冻结 |

---

## 5. 已知轻微问题

1. **Style Sweep 历史记录和运行资产会持续积累** — 后续需要清理机制（删除 job + 清理关联视频文件）
2. **前端 canPromote 主要检查 finalVideoUrl** — 若未来只有 videoUrl 没有 finalVideoUrl，需要兼容分支逻辑
3. **Style Gallery sample_id 跳转定位体验** — 可后续优化自动清除筛选器，当前为已知优化项

> 以上均不阻塞当前 Style Sweep → Style Gallery 样片库沉淀闭环冻结。

---

## 6. 当前阶段不包含

1. 批量多选提升（一次选择多个 styleId）
2. Style Sweep job 删除
3. Style Sweep 运行资产清理
4. 样片库按 sweepJobId 筛选
5. 样片库来源标签增强展示
6. 模板沉淀自动化
7. 对比包自动创建
8. promoted sample 自动评分
9. promoted sample 自动加入验证篮

---

## 7. 下一阶段建议

建议进入以下任一方向：

### 推荐：阶段 3A — Style Sweep 历史记录删除与运行资产清理

**原因**：当前 Style Sweep 已能生成、回看、提升和沉淀，但 job JSON 和视频资产会持续积累。下一步应补"删除记录 / 清理资产 / 保留已提升样片"的安全机制。

### 备选：阶段 3B — Remotion 模板差异化与背景丰富度审计

**原因**：Style Sweep 三路线中 Remotion 路线完成度最高（14 样式），但部分样式背景较为单薄，可作为后续优化方向。

---

## 8. 相关文档

- [V1.2.3 Style Sweep 验证中心基础闭环冻结记录](V1_2_3_STYLE_SWEEP_VALIDATION_BASELINE.md)
