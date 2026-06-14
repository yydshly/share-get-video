"""
html_builder.py - Generate single-file HTML video page for HeyGen HyperFrames
V0.3.2: Manual verification route

Generates a self-contained HTML file that can be pasted into
HeyGen's HyperFrames plugin for video rendering.
"""

import json
from pathlib import Path
from typing import Any

from app.video_lab.renderers.file_store import get_experiment_dir


# ─────────────────────────────────────────
# Colors (ai_frontier_dark preset)
# ─────────────────────────────────────────
C = {
    "bg": "#0a0e1a",
    "surface": "#111827",
    "card": "#1a2236",
    "accent": "#3b82f6",
    "accent2": "#8b5cf6",
    "highlight": "#f59e0b",
    "textPrimary": "#f8fafc",
    "textSecondary": "#94a3b8",
    "textMuted": "#64748b",
    "border": "#1e293b",
}


def build_html(
    experiment_id: str,
    structured: dict[str, Any],
    key_points: dict[str, Any],
    params: dict[str, Any],
) -> dict[str, Any]:
    """
    Build a self-contained HTML page for HeyGen HyperFrames.

    Args:
        experiment_id: experiment identifier
        structured: structured content (from content_structurer)
        key_points: key points (from key_point_extractor)
        params: render parameters

    Returns:
        dict with keys: success, htmlPath, htmlUrl, warnings
    """
    warnings: list[str] = []

    # Extract content
    lead = structured.get("lead", "")
    title = _extract_title(lead)
    subtitle = structured.get("subtitle", "今日 AI 前沿速览")

    kps_list = key_points.get("keyPoints", key_points.get("key_points", []))
    key_points_data = []
    for kp in kps_list:
        if isinstance(kp, dict):
            key_points_data.append({
                "title": kp.get("title", ""),
                "body": kp.get("body", ""),
                "source": kp.get("source", ""),
            })
        else:
            key_points_data.append({"title": str(kp), "body": "", "source": ""})

    if not key_points_data:
        warnings.append("No key points found — HTML may be minimal")

    # Build HTML content
    html_content = _generate_html(title, subtitle, key_points_data)

    # Write to file
    exp_dir = get_experiment_dir(experiment_id)
    hyperframes_dir = exp_dir / "hyperframes"
    hyperframes_dir.mkdir(parents=True, exist_ok=True)
    html_path = hyperframes_dir / "index.html"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    from app.video_lab.renderers.file_store import path_to_url
    html_url = path_to_url(html_path)

    return {
        "success": True,
        "htmlPath": str(html_path),
        "htmlUrl": html_url,
        "title": title,
        "keyPointCount": len(key_points_data),
        "warnings": warnings,
    }


def _generate_html(title: str, subtitle: str, key_points: list[dict]) -> str:
    """Generate the full HTML document."""
    # Serialize key points to JSON for the JS
    kps_json = json.dumps(key_points, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_escape_html(title)}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    background: {C['bg']};
    color: {C['textPrimary']};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    overflow: hidden;
    width: 100vw;
    height: 100vh;
  }}

  .page {{
    position: absolute;
    top: 0; left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 60px 48px;
    opacity: 0;
    animation: none;
  }}

  .page.visible {{
    animation: pageIn 0.6s ease-out forwards;
  }}

  @keyframes pageIn {{
    from {{ opacity: 0; transform: translateY(30px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}

  @keyframes fadeIn {{
    from {{ opacity: 0; }}
    to   {{ opacity: 1; }}
  }}

  @keyframes slideUp {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}

  /* Cover Page */
  .cover {{
    background: {C['bg']};
    text-align: center;
  }}
  .cover-glow {{
    position: absolute;
    top: 15%;
    left: 50%;
    transform: translateX(-50%);
    width: 400px; height: 400px;
    border-radius: 50%;
    background: rgba(59,130,246,0.12);
    filter: blur(80px);
    pointer-events: none;
  }}
  .cover-label {{
    position: absolute;
    top: 48px;
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: {C['accent']};
    opacity: 0;
    animation: fadeIn 0.5s 0.3s ease-out forwards;
  }}
  .cover-title {{
    font-size: 88px;
    font-weight: 800;
    line-height: 1.1;
    text-align: center;
    text-shadow: 0 0 60px rgba(59,130,246,0.25);
    max-width: 90%;
    opacity: 0;
    animation: slideUp 0.6s 0.1s ease-out forwards;
  }}
  .cover-subtitle {{
    font-size: 32px;
    color: {C['textSecondary']};
    margin-top: 24px;
    opacity: 0;
    animation: fadeIn 0.5s 0.5s ease-out forwards;
  }}
  .cover-line {{
    width: 120px; height: 4px;
    background: linear-gradient(90deg, {C['accent']}, {C['accent2']});
    border-radius: 2px;
    margin: 40px auto 0;
    opacity: 0;
    animation: slideUp 0.5s 0.7s ease-out forwards;
  }}
  .cover-footer {{
    position: absolute;
    bottom: 48px;
    font-size: 22px;
    color: {C['textMuted']};
    opacity: 0;
    animation: fadeIn 0.5s 1s ease-out forwards;
  }}

  /* KeyPoint Page */
  .keypoint {{
    background: {C['bg']};
    padding: 80px 64px;
  }}
  .kp-card {{
    width: 100%;
    max-width: 860px;
    background: {C['card']};
    border: 1px solid {C['border']};
    border-radius: 24px;
    padding: 56px 48px;
    position: relative;
    box-shadow: 0 0 80px rgba(59,130,246,0.1), 0 20px 60px rgba(0,0,0,0.5);
  }}
  .kp-card::before {{
    content: '';
    position: absolute;
    top: -1px; left: 10%; right: 10%;
    height: 2px;
    background: linear-gradient(90deg, transparent, {C['accent']}, transparent);
    border-radius: 2px;
  }}
  .kp-badge {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 60px; height: 60px;
    border-radius: 14px;
    background: linear-gradient(135deg, {C['accent']}, {C['accent2']});
    font-size: 26px;
    font-weight: 800;
    margin-bottom: 28px;
  }}
  .kp-title {{
    font-size: 68px;
    font-weight: 800;
    line-height: 1.15;
    text-shadow: 0 0 40px rgba(59,130,246,0.2);
    margin-bottom: 24px;
  }}
  .kp-body {{
    font-size: 36px;
    color: {C['textSecondary']};
    line-height: 1.5;
  }}
  .kp-source {{
    font-size: 22px;
    color: {C['textMuted']};
    margin-top: 20px;
  }}

  /* Summary Page */
  .summary {{
    background: {C['bg']};
    padding: 80px 64px;
  }}
  .summary-title {{
    font-size: 72px;
    font-weight: 800;
    text-align: center;
    margin-bottom: 48px;
    text-shadow: 0 0 40px rgba(59,130,246,0.2);
  }}
  .summary-list {{
    width: 100%;
    max-width: 900px;
  }}
  .summary-item {{
    display: flex;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 20px;
  }}
  .summary-dot {{
    width: 12px; height: 12px;
    border-radius: 50%;
    background: {C['accent']};
    margin-top: 14px;
    flex-shrink: 0;
    box-shadow: 0 0 12px {C['accent']};
  }}
  .summary-text {{
    font-size: 32px;
    color: {C['textSecondary']};
    line-height: 1.4;
  }}
  .summary-text strong {{
    color: {C['textPrimary']};
    font-weight: 700;
  }}
  .summary-glow {{
    position: absolute;
    bottom: 20%; right: 10%;
    width: 500px; height: 500px;
    border-radius: 50%;
    background: rgba(139,92,246,0.08);
    filter: blur(100px);
    pointer-events: none;
  }}

  /* Navigation dots */
  .nav-dots {{
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 8px;
    z-index: 100;
  }}
  .nav-dot {{
    width: 8px; height: 8px;
    border-radius: 50%;
    background: rgba(148,163,184,0.3);
    cursor: pointer;
  }}
  .nav-dot.active {{
    background: {C['accent']};
  }}
</style>
</head>
<body>
{_cover_page(title, subtitle)}
{_keypoint_pages(key_points)}
{_summary_page(title, key_points)}
<div class="nav-dots" id="navDots"></div>
<script>
  // ── Page Navigation ─────────────────────────────────────────────────────
  const pages = Array.from(document.querySelectorAll('.page'));
  const totalPages = pages.length;
  let currentPage = 0;

  function showPage(index) {{
    pages.forEach((p, i) => {{
      p.classList.toggle('visible', i === index);
    }});
    currentPage = index;
    updateDots();
  }}

  function updateDots() {{
    const dots = document.getElementById('navDots');
    dots.innerHTML = '';
    for (let i = 0; i < totalPages; i++) {{
      const d = document.createElement('div');
      d.className = 'nav-dot' + (i === currentPage ? ' active' : '');
      d.onclick = () => showPage(i);
      dots.appendChild(d);
    }}
  }}

  // Auto-advance every 5 seconds
  showPage(0);
  setInterval(() => {{
    showPage((currentPage + 1) % totalPages);
  }}, 5000);
</script>
</body>
</html>"""


def _cover_page(title: str, subtitle: str) -> str:
    """Generate the cover page HTML."""
    return f"""
  <div class="page cover visible">
    <div class="cover-glow"></div>
    <div class="cover-label">AI 前沿</div>
    <h1 class="cover-title">{_escape_html(title)}</h1>
    <p class="cover-subtitle">{_escape_html(subtitle)}</p>
    <div class="cover-line"></div>
    <div class="cover-footer">AI 资讯共享视频 · V0.3.2</div>
  </div>"""


def _keypoint_pages(key_points: list[dict]) -> str:
    """Generate keypoint page HTML for each key point."""
    html = ""
    for i, kp in enumerate(key_points):
        kp_title = _escape_html(kp.get("title", ""))
        kp_body = _escape_html(kp.get("body", ""))
        kp_source = _escape_html(kp.get("source", ""))
        badge_num = str(i + 1).zfill(2)
        source_html = f'<div class="kp-source">来源：{kp_source}</div>' if kp_source else ""
        html += f"""
  <div class="page keypoint">
    <div class="kp-card">
      <div class="kp-badge">{badge_num}</div>
      <h2 class="kp-title">{kp_title}</h2>
      <p class="kp-body">{kp_body}</p>
      {source_html}
    </div>
  </div>"""
    return html


def _summary_page(title: str, key_points: list[dict]) -> str:
    """Generate the summary page HTML."""
    items_html = ""
    for kp in key_points:
        kp_title = _escape_html(kp.get("title", ""))
        kp_body = _escape_html(kp.get("body", ""))
        items_html += f"""
      <div class="summary-item">
        <div class="summary-dot"></div>
        <div class="summary-text">
          <strong>{kp_title}</strong> — {kp_body}
        </div>
      </div>"""

    return f"""
  <div class="page summary">
    <div class="summary-glow"></div>
    <h2 class="summary-title">{_escape_html(title)}</h2>
    <div class="summary-list">
      {items_html}
    </div>
  </div>"""


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _extract_title(lead: str) -> str:
    """Extract a short title from the lead text."""
    if not lead:
        return "AI 前沿动态"
    sentences = lead.split("。")
    first = sentences[0].strip()
    if len(first) > 30:
        return first[:30] + "..."
    return first if first else "AI 前沿动态"
