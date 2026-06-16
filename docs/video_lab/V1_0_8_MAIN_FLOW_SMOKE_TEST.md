# V1.0.8 Video Lab Main Flow Smoke Test

## 1. 测试目标

验证 Video Lab 主流程是否形成闭环：

```
Workbench → Full Video → JobRun → Save Sample → Style Gallery → Rerun Payload → Compare → Compare Bundle
```

## 2. 测试环境

| Field | Value |
|-------|-------|
| Branch | feature/v1.0.7-compare-bundle |
| Commit | 1923c703be958d8d419128d13063798181d25409 |
| Backend URL | http://localhost:8777 |
| Frontend URL | http://localhost:5173 (or Vite dev server) |
| Python | 3.10.11 |
| Node | (run `node --version` to verify) |
| OS | Windows 11 Home China 10.0.26200 |
| 是否使用真实视频生成 | ⚠️ 需要实际启动后端确认 |
| 是否使用 Mock | ⚠️ 需要实际启动后端确认 |
| 测试时间 | [待手动填写] |

## 3. 主流程步骤

### Step 1: 打开 Video Lab 首页

**预期：**
- 能看到 Video Lab 首页
- 能看到主工作台入口
- 能看到样片库入口
- 能看到高级实验区

**结果：**
- [ ] Pass
- [ ] Fail
- 备注：

### Step 2: 进入 Workbench

**预期：**
- 页面可打开
- 能输入内容
- 能选择路线
- 能生成 preview
- preview 成功/失败都显示 JobRun

**结果：**
- [ ] Pass
- [ ] Fail
- 备注：

### Step 3: 生成 Full Video

**预期：**
- 能触发完整视频生成
- 成功时显示 finalVideoUrl
- 失败时显示 error
- 成功/失败都显示 JobRun

**结果：**
- [ ] Pass
- [ ] Fail
- 备注：

### Step 4: 保存样片

**预期：**
- 能保存为 approved / rejected
- 保存后跳转或可在 Style Gallery 看到
- 样片包含 source / generation / asset_meta / quality_meta / review_meta / job_run

**结果：**
- [ ] Pass
- [ ] Fail
- 备注：

### Step 5: Style Gallery 查看样片

**预期：**
- 样片卡片可见
- 视频或封面可预览
- 实验资产信息可见
- JobRun / manifest / route / review 信息可见

**结果：**
- [ ] Pass
- [ ] Fail
- 备注：

### Step 6: 复制 rerun payload

**预期：**
- 点击复制复现参数
- 成功显示"已复制复现参数"
- clipboard 中是完整 JSON
- JSON 包含 visualComposePayload / clipPreviewPayload

**结果：**
- [ ] Pass
- [ ] Fail
- 备注：

### Step 7: 加入对比

**预期：**
- 点击加入对比
- 样片状态变为 comparing
- 对比面板出现样片
- 无评分时显示暂无评分提示

**结果：**
- [ ] Pass
- [ ] Fail
- 备注：

### Step 8: 保存 Compare Bundle

**预期：**
- 输入 title / goal / tags
- 点击保存当前对比包
- 保存成功
- 历史对比包列表出现记录
- bundle JSON 可复制

**结果：**
- [ ] Pass
- [ ] Fail
- 备注：

### Step 9: 删除 Compare Bundle

**预期：**
- 删除历史对比包
- 列表刷新
- 删除不存在 bundle 时有合理反馈

**结果：**
- [ ] Pass
- [ ] Fail
- 备注：

## 4. 接口检查

记录以下接口是否正常：

| 接口 | 方法 | 预期状态 | 实际结果 |
|------|------|----------|----------|
| /video-lab/routes | GET | 200 | [ ] Pass [ ] Fail |
| /video-lab/clip-preview | POST | 200 | [ ] Pass [ ] Fail |
| /video-lab/visual-compose | POST | 200 | [ ] Pass [ ] Fail |
| /video-lab/style-samples | POST | 200 | [ ] Pass [ ] Fail |
| /video-lab/style-samples | GET | 200 | [ ] Pass [ ] Fail |
| /video-lab/style-samples/{id}/rerun-payload | GET | 200 | [ ] Pass [ ] Fail |
| /video-lab/style-samples/{id}/compare | POST | 200 | [ ] Pass [ ] Fail |
| /video-lab/style-compare-bundles | POST | 200 | [ ] Pass [ ] Fail |
| /video-lab/style-compare-bundles | GET | 200 | [ ] Pass [ ] Fail |
| /video-lab/style-compare-bundles/{id} | GET | 200 | [ ] Pass [ ] Fail |
| /video-lab/style-compare-bundles/{id} | DELETE | 200/404 | [ ] Pass [ ] Fail |

## 5. 资产字段检查

### 样片必须检查

| 字段 | 路径 | 检查结果 |
|------|------|----------|
| id | sample.id | [ ] Pass [ ] Fail |
| route_id | sample.route_id | [ ] Pass [ ] Fail |
| status | sample.status | [ ] Pass [ ] Fail |
| source | sample.source | [ ] Pass [ ] Fail |
| generation | sample.generation | [ ] Pass [ ] Fail |
| asset_meta | sample.asset_meta | [ ] Pass [ ] Fail |
| quality_meta | sample.quality_meta | [ ] Pass [ ] Fail |
| review_meta | sample.review_meta | [ ] Pass [ ] Fail |
| job_run | sample.job_run | [ ] Pass [ ] Fail |
| schema_version | sample.schema_version | [ ] Pass [ ] Fail |
| params.fullContent | sample.params.fullContent | [ ] Pass [ ] Fail |

### Compare Bundle 必须检查

| 字段 | 路径 | 检查结果 |
|------|------|----------|
| id | bundle.id | [ ] Pass [ ] Fail |
| title | bundle.title | [ ] Pass [ ] Fail |
| goal | bundle.goal | [ ] Pass [ ] Fail |
| sample_ids | bundle.sample_ids | [ ] Pass [ ] Fail |
| items | bundle.items | [ ] Pass [ ] Fail |
| decision | bundle.decision | [ ] Pass [ ] Fail |
| winner_sample_id | bundle.decision.winner_sample_id | [ ] Pass [ ] Fail |
| winner_reason | bundle.decision.winner_reason | [ ] Pass [ ] Fail |
| tags | bundle.tags | [ ] Pass [ ] Fail |
| schema_version | bundle.schema_version | [ ] Pass [ ] Fail |

## 6. 问题记录

| 编号 | 严重级别 | 页面/接口 | 问题 | 是否阻塞 | 建议版本 |
|------|----------|----------|------|----------|----------|
| （待填写） | | | | | |

## 7. 验收结论

- [ ] V1.0.8 Pass
- [ ] V1.0.8 Pass with minor issues
- [ ] V1.0.8 Fail

**结论说明：**
（待手动填写）

## 8. 下一步建议

（待手动填写，根据验收结果决定）

---

## 附录：自动化测试覆盖范围

本版本新增了 `tests/test_video_lab_main_flow_smoke.py`，覆盖以下场景：

1. ✅ 创建带完整 V1.0.5 资产字段的 StyleSample 并保存
2. ✅ 调用 `get_style_sample_rerun_payload` 返回 schemaVersion=1.0.6
3. ✅ rerun payload 的 `visualComposePayload.content` 来自 `params.fullContent`
4. ✅ 标记样片为 comparing 状态
5. ✅ 创建 CompareBundle，schemaVersion=1.0.7
6. ✅ bundle.items 包含对应 sample
7. ✅ winner 逻辑（score 最高者胜出，无 score 时说明需人工判断）
8. ✅ 删除 bundle 后 GET 返回 404
9. ✅ 部分无效 sample_id 时跳过不崩溃
10. ✅ 全部无效 sample_id 时返回空 bundle

**自动化测试不覆盖（需手动验证）：**
- 真实 UI 渲染（Workbench 页面、Style Gallery 页面）
- 真实视频生成流程
- 真实 clipboard 操作
- 真实 JobRun 状态展示
