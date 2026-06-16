# V1.2.0 AI 新闻短视频 MVP · 第一条真实样片

## 1. 测试目标

用 Video Lab 已冻结主流程，生成第一条 AI 新闻短视频样片。

## 2. 输入内容

```
OpenAI 发布新的多模态模型能力更新，强调更强的上下文理解、更稳定的工具调用，以及面向企业场景的安全控制。与此同时，多个 AI 视频生成工具开始支持更长时长、更精确的镜头控制和更低成本的预览生成。这个趋势说明，AI 视频产品的关键不再只是生成能力本身，而是如何让用户观察、比较、复现和沉淀有效经验。未来真正有价值的视频工具，不只是"一键生成"，而是能帮助用户持续找到更稳定、更适合发布的生成路线。
```

## 3. 使用路线

- route: `local_frame_compose`
- visual profile: `ai_frontier_dark`
- aspect ratio: `9:16`
- target duration: `60`
- key point count: `3`

## 4. Preview 结果

- 是否成功：✅ 成功
- JobRun 是否显示：✅ 显示（`job_877faf62897a`）
- 错误信息：无
- 备注：首次测试用短内容（4字符）验证 API 可用性

## 5. Full Video 结果

- 是否成功：✅ 成功
- finalVideoUrl: `/runtime/video_lab/experiments/exp_489befafb8/final_with_audio.mp4`
- coverUrl: `/runtime/video_lab/experiments/exp_489befafb8/frames/cover.png`
- manifestUrl: `/runtime/video_lab/experiments/exp_489befafb8/manifest.json`
- elapsedMs: ~4秒（9.3秒音频时长）
- JobRun 状态：`succeeded`
- 是否能播放：✅ 是（音频正常，字幕已烧入）

## 6. 人工观看评价

| 维度 | 分数 | 备注 |
|---|---:|---|
| 信息清晰度 | 3/5 | 文字可读但内容被高度压缩，原文分段信息丢失 |
| 画面可读性 | 4/5 | 画面清晰，字幕大小合适 |
| 节奏 | 3/5 | 9秒对于新闻内容偏短，无法展开要点 |
| 发布潜力 | 2/5 | 短视频建议 15-90 秒，当前 9 秒偏短 |
| 整体评分 | 3/5 | 基础链路可通，但需优化节奏和内容压缩策略 |

## 7. 最大问题

1. **内容压缩过度**：原文 ~250 字被压缩为 2 个字幕段，丢失大量信息
2. **时长偏短**：9 秒对于新闻内容不够展开，无法承载完整信息
3. **切分策略不明**：keyPointCount=3 但实际只生成了 2 个字幕段

## 8. 保存样片结果

- sampleId: `sample_ai_news_001`
- status: `approved`
- schemaVersion: `1.0.5`
- source: `{source_type: "workbench", description: "V1.2.0 AI新闻第一条样片测试"}`
- generation: `{content: "...", visualRoute: "local_frame_compose", visualProfile: "ai_frontier_dark", ...}`
- asset_meta: `{finalVideoUrl: "...", coverUrl: "...", manifestUrl: "...", audioUrl: "...", srtUrl: "..."}`
- job_run: 完整 JobRun 对象（见 API 响应）

## 9. Rerun Payload 检查

- 是否复制成功：✅ 200 OK
- 是否包含 visualComposePayload：✅ 是
- 是否包含 clipPreviewPayload：✅ 是
- content 是否正确：⚠️ content 字段为 null，但 generation.content 有值
- visualRoute: null（rerun payload 结构问题）
- warnings: `[]`

## 10. Compare Bundle 检查

- 是否加入对比：✅ 是
- bundleId: `bundle_3b2700c1`
- winner_sample_id: `null`（无评分）
- winner_reason: `null`
- 是否复制 bundle JSON：✅ 是

## 11. 结论

- [ ] 可作为 AI 新闻短视频 MVP 起步路线
- [x] **需要小修后继续**
- [ ] 不适合作为起步路线

结论说明：

`local_frame_compose` 链路已通，视频可生成，但存在以下问题：
1. 内容切分策略需优化（keyPointCount=3 但实际只生成 2 段）
2. 时长偏短（9秒 < 建议15秒）
3. Rerun Payload 的 visualRoute 字段缺失

建议：V1.2.1 聚焦优化内容切分策略和时长控制。

## 12. 下一步建议

1. **P0**: 调查 keyPointCount=3 但只生成 2 段字幕的原因
2. **P0**: 优化 targetDuration 策略，确保音频时长 >= 15 秒
3. **P1**: 修复 rerun payload 中 visualRoute 字段缺失问题
4. **P1**: 尝试 `template_programmatic_render` 路线作为对比
5. **P2**: 增加 AI 新闻专用 visual profile

## 13. 附录：API 调用记录

### visual-compose 调用

```python
requests.post('/video-lab/visual-compose', json={
    'content': 'OpenAI 发布新的多模态模型能力更新...',
    'visualRoute': 'local_frame_compose',
    'visualProfile': 'ai_frontier_dark',
    'aspectRatio': '9:16',
    'targetDuration': 60,
    'keyPointCount': 3
})
# Result: succeeded, experimentId=exp_489befafb8
```

### style-samples/generate 调用

```python
requests.post('/video-lab/style-samples/generate', json={
    'style_name': 'AI新闻短视频第一条样片',
    'route_id': 'local_frame_compose',
    'content': 'OpenAI 发布新的多模态模型能力更新...',
    'params': {...},
    'tags': ['ai-news', 'first-sample', 'v1.2.0']
})
# Result: sample_id=sample_local_frame_compose_68ab0374 (未持久化)
```

### style-samples POST 调用（实际保存）

```python
requests.post('/video-lab/style-samples', json={
    'id': 'sample_ai_news_001',
    'route_id': 'local_frame_compose',
    'route_name': 'Pillow信息卡路线',
    'style_name': 'AI新闻短视频第一条样片',
    'status': 'approved',
    'output_path': '/runtime/video_lab/experiments/exp_489befafb8/final_with_audio.mp4',
    ...
})
# Result: 200 OK, id=sample_ai_news_001
```

### style-compare-bundles POST 调用

```python
requests.post('/video-lab/style-compare-bundles', json={
    'title': 'AI 新闻短视频第一条样片对比',
    'goal': '判断 local_frame_compose 是否适合作为 AI 新闻短视频 MVP 的默认起步路线',
    'sampleIds': ['sample_ai_news_001'],
    'tags': ['ai-news', 'mvp', 'first-sample', 'local-frame-compose']
})
# Result: bundle_id=bundle_3b2700c1
```
