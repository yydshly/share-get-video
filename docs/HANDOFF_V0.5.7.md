# share-get-video 交接说明（截至 V0.5.7）

> 给接手的大模型：这是一个"视频能力实验室 / 风格画廊"项目，目标是探索**哪种视频生成技术**最适合把一段 AI 新闻摘要变成优雅的可分享竖屏短视频(9:16)。三条技术路线并行对比。

## 仓库 / 分支
- repo: https://github.com/yydshly/share-get-video
- 工作分支: `feature/v0.3.6-b1-shotplan-standardization`
- 最新 commit: `8b6323d V0.5.7`
- 工作区干净，所有改动已 push

## 严格执行规则（必须遵守）
1. 先检查当前分支、工作区、远端状态
2. 不要直接相信报告，改完必须提交和推送
3. 每轮只做一个小闭环
4. 不要扩散到模板市场、用户系统、数据库
5. 不提交视频、音频、大文件产物（runtime/ 已 gitignore）
6. 所有新增能力都要有测试
- 每轮跑：`python -m compileall app/ -q`、相关 pytest、`cd frontend && npm run typecheck`、`cd remotion && npx tsc --noEmit`，然后 commit + `git push origin feature/v0.3.6-b1-shotplan-standardization`
- commit 尾部加 `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- **每步修改都要渲染出帧、肉眼看效果**（用户明确要求"看到每一步修改的效果"）

## 核心方向（用户反复强调）
核心是 **①生成视频的能力 + ②不同样式生成视频的效果查看**，别跑偏去做辅助/元数据功能。内容层先保准确。

## 三条视觉路线
- `local_frame_compose` (Pillow 静态卡 + Ken Burns)
- `template_programmatic_render` (Remotion 动效：数字滚动/数据条/转场)
- `ai_asset_then_compose` (MiniMax 生图做背景 + 叠卡)

## 流水线
report → LLM规划(plan_shots: headline/display/narration/emphasisTerms/tone/metrics) → key_points → 旁白 → MiniMax TTS → 字幕(SRT/ASS,按真实音频重对齐) → 视觉渲染器(出静默视频) → FFmpeg合成(音频+字幕烧录+BGM) → 终片

## 已完成的体检（本阶段 V0.5.4–V0.5.7）
- **V0.5.4**: Pillow 总结页列表垂直居中、留白平衡
- **V0.5.5**: Remotion 关键点卡 minHeight 1100→760 + flex 居中，消除卡片下半固定空白
- **V0.5.6**: Remotion editorial 封面 justifyContent flex-start→center，竖屏垂直居中
- **V0.5.7**: 规划器 headline 上限 18→24（HEADLINE_MAX），避免"ProReviewer论文评审系统发布"等 19 字标题被截成"…"

### 路线体检状态
| 路线 | 单帧/页面 | LLM真实内容 | 带音频整片 |
|---|---|---|---|
| Pillow | ✅ 封面/关键点/总结/数据卡/跨行高亮 | 部分 | ⬜ **未做** |
| Remotion | ✅ 三页竖屏平衡 | ✅ 内容准确、tone区分(绿↑/琥珀!) | ✅ 49s整片、字幕烧录、节奏对齐音频 |
| AI素材 | ⬜ **未系统看过** | ⬜ | ⬜ |

## 待办候选（用户上次倾向 1）
1. **Pillow 带音频整片**，和 Remotion 整片对比（落到项目目标③"多技术对比"）
2. **AI 素材路线逐页体检**（唯一没系统看过的路线，需图像API）
3. **内容冗余**：卡片正文(display)与字幕(narration)语义几乎重复，可让正文更精炼/差异化

## 已知非阻塞问题
- plan dict 里 `usedLlm` 字段未被赋值(显示None)，但 `source:llm` 正确——纯字段冗余
- Pillow 多要点长文本(4-6条超长正文)的溢出/截断未压测过

## 关键文件
- `app/video_lab/planners/llm_content_planner.py` — plan_shots / _extract_metrics / _clamp / HEADLINE_MAX=24
- `app/video_lab/renderers/frame_templates.py` (~1050行) — Pillow 模板：render_cover/keypoint/summary_template、_draw_lines_with_highlights(跨行高亮)
- `app/video_lab/renderers/frame_preview.py` — render_single_frame / render_clip_preview（体检用，秒级单帧 + Remotion短片）
- `app/video_lab/renderers/theme_presets.py` — tone→配色/图标 (positive绿↑/negative琥珀!/neutral蓝✦)
- `app/video_lab/adapters/tts_subtitle_compose.py` — run_tts_subtitle_compose（完整9步整片）
- `remotion/src/AiNewsVideo.tsx` (~1100行) — CoverPage/KeyPointCard/SummaryPage + 动效组件
- `app/video_lab/router.py` (~1100行) — 所有 style-gallery / frame-preview / clip-preview 端点
- `frontend/src/video-lab/pages/StyleGalleryPage.tsx`、`FramePreviewPage.tsx` — 浏览器入口

## 常用体检命令（环境 win32, bash, MINIMAX_API_KEY 已配）
```bash
# 单帧快速预览(Pillow, 秒级, 无API)
python -c "from dotenv import load_dotenv; load_dotenv(); from app.video_lab.renderers.frame_preview import render_single_frame; print(render_single_frame('local_frame_compose','keypoint',{'headline':'标题','display':'正文','emphasisTerms':['39%']},'',{'themeAdaptive':True,'showDataViz':True}))"

# Remotion 短片(无API, ~26s)
python -c "from dotenv import load_dotenv; load_dotenv(); from app.video_lab.renderers.frame_preview import render_clip_preview; print(render_clip_preview(open('内容.txt',encoding='utf-8').read(),'template_programmatic_render',{'keyPointCount':3,'useLlmPlan':False},clip_seconds=14))"

# 带音频整片(需TTS, ~1-2min)
python -c "from dotenv import load_dotenv; load_dotenv(); import uuid; from app.video_lab.adapters.tts_subtitle_compose import run_tts_subtitle_compose; run_tts_subtitle_compose('full_'+uuid.uuid4().hex[:8],'ai_insight_summary',{'content':open('内容.txt',encoding='utf-8').read()},{'visualRoute':'template_programmatic_render','useLlmPlan':True,'keyPointCount':3,'aspectRatio':'9:16','targetDuration':30})"

# 从视频抽帧肉眼看
ffmpeg -y -i runtime/.../clip.mp4 -vf "select=eq(n\,160)" -vframes 1 D:/tmp/x.png -loglevel error
```
> 注意：Windows 终端是 GBK，Python print 中文会乱码（仅显示问题，数据正常）；渲染出的图片用看图确认。

## 测试
`tests/test_style_gallery_*.py`、`test_frame_preview_faithful.py`、`test_cross_line_highlight.py`、`test_keypoint_metrics_layout.py`、`test_llm_content_planner.py` 等。跑全套示例见执行规则。
