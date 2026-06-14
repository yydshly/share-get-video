#!/usr/bin/env python
"""
compare_video_routes.py - 视频生成能力对比入口

一个入口：投入同一份 AI 资讯报告 → 用不同视觉技术路线各生成一个最终视频 →
输出对比结果。内容保持一致（共享上游结构化），便于横向比较"信息准确 + 画面效果"。

用法：
    # 用默认内置样例，对比 Pillow 与 Remotion 两条视觉路线
    python scripts/compare_video_routes.py

    # 指定报告文件 + 指定路线 + 时长
    python scripts/compare_video_routes.py \
        --input report.txt \
        --routes local_frame_compose,template_programmatic_render \
        --duration 45 --aspect 9:16

依赖：
    - FFmpeg（所有路线需要合成）
    - MINIMAX_API_KEY（TTS 旁白）
    - Node.js + remotion（仅 template_programmatic_render 路线需要）

输出：
    runtime/video_lab/comparisons/<timestamp>/comparison.json
    控制台对比表（状态 / 最终视频 / 时长 / 字幕 / 失败原因）
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Windows 控制台默认 GBK，强制 UTF-8 输出避免中文/符号报错
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from app.video_lab.adapters.tts_subtitle_compose import run_tts_subtitle_compose
from app.video_lab.renderers.visual import list_visual_renderers


DEFAULT_REPORT = """今日AI前沿呈现多条并行进展线索：多语言NLP在低资源方言、科学事实检测等领域取得突破，阿尔及利亚方言谣言检测混合框架F1达0.84；AI评估体系向多维化和精细化演进，购物推理、长期搜索、立场复杂度等新基准揭示主流模型显著短板；安全对齐方面，主动调查评审、欺骗检测等新范式推动可扩展监督研究；企业级AI落地加速，Anthropic与TCS/DXC合作进入受监管行业，DeepMind千万美元投入多智能体安全研究。整体来看，研究重心正从单一性能提升转向可信性、可靠性和跨文化鲁棒性的综合评估。

科学研究评审实现"主动调查"突破：ProReviewer系统将评审建模为马尔可夫决策过程，在五个质量维度超越提示工程方法39%，为AI辅助学术评审提供新范式。
依据： 依据 1
欺骗检测新范式：RogueAI将信任问题转化为"审问游戏"，玩家需在有限回合内识别人机混合对话中的欺骗者，为可扩展监督和LLM欺骗检测开辟新思路。
依据： 依据 1
购物AI助手全面落后主流模型：Shopping Reasoning Bench测评发现GPT、Claude、Gemini系列通过率仅57-77%，多轮场景下所有模型表现更差，暴露复杂推理短板。
依据： 依据 1
立场检测揭示"相变"规律：SICI复杂度指数发现LLM错误模式随复杂度呈现三阶段相变——低复杂度过度归因、中等复杂度不稳定、高复杂度集中无立场，为立场检测提供诊断工具。
依据： 依据 1
AI同行评审存在"展示层"攻击漏洞：攻击者可仅修改摘要措辞、相关工作定位等展示层面内容，实现75.1%攻击成功率，对高校AI审稿政策提出警示。
依据： 依据 1
企业级AI加速进入受监管行业：Anthropic与TCS、DXC建立全球联盟，Claude进入银行、航空等高合规要求领域，DeepMind宣布千万美元多智能体安全研究投资。
依据： 依据 1 依据 2 依据 3
"""

DEFAULT_ROUTES = ["local_frame_compose", "template_programmatic_render"]


def _extract_final(result) -> dict:
    """从 adapter 结果提取对比所需字段。"""
    raw = getattr(result, "rawOutput", {}) or {}
    assets = getattr(result, "assets", {}) or {}
    status = raw.get("status", "unknown")
    failed_reason = ""
    if status != "succeeded":
        # 找第一个失败步骤
        for step in getattr(result, "productionSteps", []):
            if getattr(step, "status", None) and step.status.value == "failed":
                failed_reason = step.outputSummary or step.name
                break
        failed_reason = failed_reason or raw.get("error", "")
    quality = raw.get("quality", {})
    return {
        "status": status,
        "finalVideoUrl": getattr(result, "videoUrl", "") or "",
        "coverUrl": getattr(result, "coverUrl", "") or "",
        "audioDurationSec": assets.get("audioDurationSec", 0),
        "subtitleCount": assets.get("subtitleCount", 0),
        "subtitleBurned": assets.get("subtitleBurned", False),
        "qualityScore": quality.get("overallScore"),
        "qualityDimensions": quality.get("dimensionScores", {}),
        "qualityCounts": quality.get("counts", {}),
        "quality": quality,
        "failedReason": failed_reason,
        "warnings": raw.get("warnings", []),
    }


def _rel_src(url: str) -> str:
    """把 /runtime/... URL 转成相对 comparison.html 的相对路径（本地直接打开可播放）。

    html 位于 runtime/video_lab/comparisons/<batch>/ ，上溯 3 级即到 runtime/ 。
    """
    if not url:
        return ""
    if url.startswith("/runtime/"):
        return "../../../" + url[len("/runtime/"):]
    if url.startswith("runtime/"):
        return "../../../" + url[len("runtime/"):]
    return url


def _status_color(status: str) -> str:
    return {"pass": "#3fb950", "warn": "#d29922", "fail": "#f85149"}.get(status, "#8b949e")


def write_comparison_html(out_dir: Path, comparison: dict, results: list[dict]) -> Path:
    """生成并排预览页：每条路线 视频 + 质量分 + 未通过检查。"""
    cards = []
    for r in results:
        route = r["route"]
        status = r["status"]
        q = r.get("qualityScore")
        video_src = _rel_src(r.get("finalVideoUrl", ""))
        cover_src = _rel_src(r.get("coverUrl", ""))

        if video_src:
            media = (
                f'<video controls preload="metadata" poster="{cover_src}" '
                f'style="width:100%;border-radius:8px;background:#000;max-height:70vh">'
                f'<source src="{video_src}" type="video/mp4">您的浏览器不支持视频播放</video>'
            )
        else:
            media = f'<div class="failbox">未生成视频<br><small>{r.get("failedReason","")}</small></div>'

        dims = r.get("qualityDimensions", {}) or {}
        dim_html = " · ".join(f'{k}: <b>{v}</b>' for k, v in dims.items())

        checks_html = ""
        for c in (r.get("quality", {}) or {}).get("checks", []):
            if c["status"] != "pass":
                checks_html += (
                    f'<li><span style="color:{_status_color(c["status"])}">[{c["status"]}]</span> '
                    f'{c["dimension"]}/{c["checkId"]}: {c["message"]}</li>'
                )
        checks_block = f'<ul class="checks">{checks_html}</ul>' if checks_html else '<p class="ok">全部检查通过 ✓</p>'

        q_badge = f'<span class="qbadge">质量 {q}/5</span>' if q is not None else ''
        cards.append(f"""
        <div class="card">
          <div class="card-head">
            <h2>{route}</h2>
            <div>{q_badge} <span class="status status-{status}">{status}</span></div>
          </div>
          {media}
          <p class="dims">{dim_html}</p>
          {checks_block}
        </div>""")

    html = f"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<title>视频生成路线对比 {comparison['batchId']}</title>
<style>
  body{{margin:0;background:#0d1117;color:#e6edf3;font-family:system-ui,'Microsoft YaHei',sans-serif}}
  header{{padding:16px 24px;border-bottom:1px solid #21262d}}
  header h1{{margin:0 0 4px;font-size:18px}} header p{{margin:0;color:#8b949e;font-size:13px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:20px;padding:24px}}
  .card{{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:16px}}
  .card-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}}
  .card-head h2{{margin:0;font-size:15px;font-family:monospace}}
  .qbadge{{background:#1f6feb;color:#fff;padding:2px 8px;border-radius:10px;font-size:12px}}
  .status{{padding:2px 8px;border-radius:10px;font-size:12px}}
  .status-succeeded{{background:#238636;color:#fff}} .status-failed,.status-exception{{background:#da3633;color:#fff}}
  .dims{{color:#8b949e;font-size:12px;margin:12px 0 6px}}
  .checks{{margin:6px 0 0;padding-left:18px;font-size:12px;color:#c9d1d9;line-height:1.6}}
  .ok{{color:#3fb950;font-size:13px}}
  .failbox{{background:#21262d;border:1px dashed #f85149;border-radius:8px;padding:32px;text-align:center;color:#f85149}}
</style></head>
<body>
<header>
  <h1>视频生成路线对比 · {comparison['batchId']}</h1>
  <p>时长 {comparison['duration']}s · 比例 {comparison['aspect']} · 内容 {comparison['contentChars']} 字 · 同一份内容横向对比</p>
</header>
<div class="grid">{''.join(cards)}</div>
</body></html>"""

    html_path = out_dir / "comparison.html"
    html_path.write_text(html, encoding="utf-8")
    return html_path


def main() -> int:
    parser = argparse.ArgumentParser(description="对比不同视觉技术路线的视频生成能力")
    parser.add_argument("--input", help="报告文本文件路径（UTF-8）；不指定则用内置样例")
    parser.add_argument("--routes", help="逗号分隔的视觉路线 routeId 列表", default=",".join(DEFAULT_ROUTES))
    parser.add_argument("--duration", type=int, default=45, help="目标时长（秒）")
    parser.add_argument("--aspect", default="9:16", help="画面比例 9:16 / 16:9 / 1:1")
    parser.add_argument("--list-routes", action="store_true", help="只列出可用视觉路线后退出")
    args = parser.parse_args()

    if args.list_routes:
        for r in list_visual_renderers():
            mark = "[OK]" if r["available"] else "[--]"
            print(f"  {mark} {r['routeId']:<32} {r['displayName']}  ({r['availabilityMessage']})")
        return 0

    content = Path(args.input).read_text(encoding="utf-8") if args.input else DEFAULT_REPORT
    routes = [r.strip() for r in args.routes.split(",") if r.strip()]

    known = {r["routeId"] for r in list_visual_renderers()}
    for r in routes:
        if r not in known:
            print(f"[warn] 未知视觉路线: {r}（将由链路回退到默认路线）")

    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path("runtime/video_lab/comparisons") / batch_id
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== 视频生成能力对比 [{batch_id}] ===")
    print(f"内容长度: {len(content)} chars | 路线: {routes} | 时长: {args.duration}s | 比例: {args.aspect}\n")

    results = []
    for route in routes:
        exp_id = f"cmp_{route}_{uuid.uuid4().hex[:8]}"
        params = {
            "targetDuration": args.duration,
            "aspectRatio": args.aspect,
            "visualRoute": route,
        }
        print(f"[run] route={route} exp_id={exp_id} ...")
        try:
            result = run_tts_subtitle_compose(
                experiment_id=exp_id,
                test_case_id="case_ai_frontier_daily_001",
                input_payload={"content": content},
                params=params,
            )
            summary = _extract_final(result)
        except Exception as e:  # 单条路线失败不影响其它路线
            summary = {"status": "exception", "failedReason": str(e),
                       "finalVideoUrl": "", "audioDurationSec": 0, "subtitleCount": 0}
        summary["route"] = route
        summary["experimentId"] = exp_id
        results.append(summary)
        print(f"      => {summary['status']}  {summary.get('finalVideoUrl') or summary.get('failedReason')}\n")

    # 写对比清单
    comparison = {
        "batchId": batch_id,
        "createdAt": datetime.utcnow().isoformat(),
        "duration": args.duration,
        "aspect": args.aspect,
        "contentChars": len(content),
        "routes": results,
    }
    (out_dir / "comparison.json").write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    html_path = write_comparison_html(out_dir, comparison, results)

    # 控制台对比表
    print("=== 对比结果 ===")
    print(f"{'route':<30}{'status':<11}{'quality':<9}{'dur':<7}{'subs':<6}final/reason")
    for r in results:
        detail = r.get("finalVideoUrl") or r.get("failedReason", "")
        q = r.get("qualityScore")
        q_str = f"{q}" if q is not None else "-"
        print(f"{r['route']:<30}{r['status']:<11}{q_str:<9}{str(r.get('audioDurationSec','')):<7}{str(r.get('subtitleCount','')):<6}{detail}")

    # 质量维度明细
    for r in results:
        if r.get("qualityScore") is not None:
            print(f"\n[{r['route']}] 质量 {r['qualityScore']}/5  维度: {r.get('qualityDimensions')}  检查: {r.get('qualityCounts')}")
            for c in r.get("quality", {}).get("checks", []):
                if c["status"] != "pass":
                    print(f"    [{c['status']}] {c['dimension']}/{c['checkId']}: {c['message']}")

    print(f"\n对比清单: {out_dir / 'comparison.json'}")
    print(f"预览页面: {html_path}  （双击用浏览器打开即可看视频）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
