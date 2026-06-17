# V1.2.3 Style Sweep 验证中心基础闭环冻结记录

## 1. 阶段结论

V1.2.3 Style Sweep 验证中心基础闭环已通过统一验收。

Style Sweep 已从"能批量跑样式"提升为：
- **能生成** — Pillow / AI 素材 / Remotion 三路线均可产出结果
- **能看进度** — job 轮询 + currentStyleName 实时展示
- **能提前查看增量结果** — 增量 results 可在 job 完成前提前出现
- **能回看历史** — 历史 job 列表可见，可重新打开
- **能保存人工标注** — manualMarks 可通过 API 持久化
- **能恢复人工判断** — 重新打开历史 job 后标注数据完整恢复
- **能输出排查信息** — subtitleDiagnostics 存在于 rawOutput.subtitleDiagnostics

---

## 2. 基线信息

| 项目 | 值 |
|------|-----|
| 分支 | feature/v1.2.3-style-gallery-validation-center |
| 基线 commit | b0adfc359bbb05af87c7266fafcf29e3fc7cd0b9 |
| 验收页面 | http://localhost:3000/video-lab/style-sweep |
| 后端端口 | 8777 |
| 前端端口 | 3000 |
| 验收方式 | Playwright 自动化 / API 验证 |

---

## 3. 已完成能力清单

1. Style Sweep job 进度展示
2. Job 轮询与增量结果展示
3. currentStyleName 展示
4. request.params 传入 job runner
5. job runner 与旧 /style-sweep 参数合并逻辑一致
6. job JSON 保存到 runtime/video_lab/style_sweep/jobs
7. 字幕 P0：不丢字、不截断
8. 字幕 P1：subtitleStyle 与 subtitleDiagnostics
9. visual_route 提前解析，避免 Step 6 UnboundLocalError
10. 历史 job 列表
11. 打开历史 job
12. manualMarks 持久化
13. 打开历史 job 后恢复人工标注
14. 复制报告使用当前 issueMarks

---

## 4. 三条路线验收结果

### Pillow 静态卡

| 项目 | 值 |
|------|-----|
| 典型 job | sweep_30d80edad1f5 |
| 结果 | 5/5 成功 |
| 进度 | running 1/5 → completed 5/5 |
| 字幕 | 正常 |
| subtitleDiagnostics | 存在于 rawOutput.subtitleDiagnostics |

### AI 素材 + 合成

| 项目 | 值 |
|------|-----|
| 结果 | 可生成 |
| 进度 | 可见 |
| 增量结果 | 可提前出现 |
| 字幕 | 未发现丢字 |
| subtitleDiagnostics | 存在于 rawOutput.subtitleDiagnostics |

> **注**：AI 素材路线的字幕遮挡主体问题后续建议继续人工抽看样片，但不阻塞当前阶段冻结。

### Remotion 动效

| 项目 | 值 |
|------|-----|
| 结果 | 14 样式完成 |
| 进度 | 可见 |
| currentStyleName | 可见 |
| 历史 job | 可打开 |
| 视频 | 可播放 |
| 明显阻塞问题 | 无 |

---

## 5. 历史回看与标注持久化验收

- 最近 Sweep 记录可见
- 打开历史 job 可恢复 results
- 打开历史 job 不需要重新生成
- `PATCH /style-sweep-jobs/{job_id}/marks` 可保存 manualMarks
- `GET /style-sweep-jobs/{job_id}` 可恢复 manualMarks
- 复制报告使用当前 issueMarks

**manualMarks 保存示例：**

```json
{
  "pillow_data_card": {
    "issues": ["ok"],
    "note": "test"
  }
}
```

---

## 6. 已知轻微问题

1. **端口占用**：本地可能存在旧 uvicorn 进程占用 8777 端口，需要重启清理。
2. **subtitleDiagnostics 位置**：当前位于 `result.rawOutput.subtitleDiagnostics`，不在顶层 `result.subtitleDiagnostics`。
3. **UI 瞬时反馈**：Playwright 自动化未稳定捕获"已保存标注"瞬时反馈文字，但 API 已验证保存成功。

> 以上均不阻塞 V1.2.3 Style Sweep 基础闭环冻结。

---

## 7. 当前阶段不包含的功能

1. Style Sweep 结果一键提升到 Style Gallery 样片库
2. 选择部分样式运行
3. 快速预览模式
4. job 取消
5. job 清理 / 删除
6. Remotion 模板差异化优化
7. 报告型正文不省略优化
8. AI 素材视觉质量优化
9. 字幕人工编辑器
10. 数据库化 job 存储

---

## 8. 下一阶段建议

建议下一阶段进入：

> **阶段 2：Style Sweep 结果提升到 Style Gallery 样片库**

**原因**：Style Sweep 已经可以完成批量探索和人工判断，但有效样式还停留在 sweep job 结果里。下一步应支持将确认有效的样式结果沉淀为 Style Gallery 样片，进入对比包、模板沉淀和后续分享链路。

**推荐提交信息**：

```bash
docs(style-sweep): freeze v1.2.3 validation baseline
```

---

## 9. 禁止事项

本任务只做文档冻结，不开发新功能。

禁止：
1. 不改后端接口
2. 不改前端 UI
3. 不改字幕逻辑
4. 不改 Style Sweep job 逻辑
5. 不改 Style Gallery
6. 不改 Remotion
7. 不改 AI 素材生成
8. 不新增测试
9. 不重跑大规模生成
