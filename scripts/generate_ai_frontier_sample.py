#!/usr/bin/env python
"""
generate_ai_frontier_sample.py - V0.2.5
Generate a real sample using case_ai_frontier_daily_001 with recommended parameters.

Usage:
    python scripts/generate_ai_frontier_sample.py

Requirements:
    - FastAPI server must be running (default: http://localhost:8000)
    - FFmpeg must be available in PATH

Output:
    - experiment_id
    - videoUrl / coverUrl / manifestUrl
    - runtime directory path
    - Does NOT commit runtime artifacts to git
"""

import requests
import sys
import os

# ─────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────
API_BASE = os.environ.get("VITE_API_BASE", "http://localhost:8000/video-lab")
TEST_CASE_ID = "case_ai_frontier_daily_001"
METHOD_ID = "method_local_frame_compose"
EXPERIMENT_TITLE = "AI前沿资讯样例-V0.2.5"

# Recommended parameters (V0.2.5)
RECOMMENDED_PARAMS = {
    "targetDuration": 45,
    "aspectRatio": "9:16",
    "keyPointCount": 6,
    "highlightMode": "auto",
    "transitionEnabled": True,
    "transitionFrames": 4,
    "stylePreset": "ai_frontier_dark",
}

# Default content for case_ai_frontier_daily_001
DEFAULT_CONTENT = """今日AI前沿呈现多维度进展：评估体系方面，多个针对科学推理、地理空间分析、UI用户体验的基准测试集中发布，同时学界开始质疑多智能体系统的实际优势；安全维度上，代理型AI框架的安全漏洞引发关注，人在循环中的研究架构被证明能显著降低失败率；应用层面，开源医学视觉语言模型OpenMedQ超越80倍规模的竞品，BBVA宣布10万员工规模化部署ChatGPT Enterprise，OpenAI则通过收购Ona强化企业级代理能力。技术优化方向上，LoRA缩放因子的深层机制和光学脉冲神经网络成为亮点。

多智能体系统未必优于单智能体：研究发现在推理和交互任务中，自动MAS成本高出10倍却表现更差，揭示当前多智能体协作方法的根本局限
依据：依据 1

代理型AI框架存在严重安全漏洞：主流框架均未实现内存完整性，单次污染攻击可使政府福利代理的错误拒绝率飙升至88.9%
依据：依据 1

人在循环中架构可将AI辅助研究失败率从72%降至16%，证明人机认知劳动的结构化分工比模型能力本身更关键
依据：依据 1

OpenMedQ以完全开源数据训练，在医学视觉问答上超越参数量达5620亿的Med-PaLM M系列，宏F1均值优于主流开源模型
依据：依据 1

BBVA宣布将ChatGPT Enterprise部署至全部约10万名员工，成为金融行业大规模生成式AI应用的标志性案例
依据：依据 1

OpenAI收购Ona以强化Codex产品线的安全持久云执行环境，拓展企业级长时间运行AI代理市场
依据：依据 1"""


def check_ffmpeg():
    """Check if FFmpeg is available."""
    import subprocess
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            version_line = result.stdout.split("\n")[0]
            print(f"  ✓ FFmpeg found: {version_line}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    print("  ✗ FFmpeg not found in PATH")
    print("    Please install FFmpeg: https://ffmpeg.org/download.html")
    print("    On Windows: winget install ffmpeg or choco install ffmpeg")
    print("    On macOS: brew install ffmpeg")
    print("    On Linux: sudo apt install ffmpeg (or equivalent)")
    return False


def check_server():
    """Check if the API server is running."""
    try:
        resp = requests.get(f"{API_BASE}/test-cases", timeout=5)
        if resp.status_code == 200:
            print(f"  ✓ API server reachable: {API_BASE}")
            return True
    except requests.exceptions.ConnectionError:
        pass
    except requests.exceptions.Timeout:
        pass
    print(f"  ✗ Cannot connect to API server: {API_BASE}")
    print("    Please start the server first:")
    print("    uvicorn app.main:app --reload --port 8000")
    return False


def build_sample_request():
    """Build the sample experiment request."""
    return {
        "testCaseId": TEST_CASE_ID,
        "methodId": METHOD_ID,
        "title": EXPERIMENT_TITLE,
        "inputPayload": {"content": DEFAULT_CONTENT},
        "params": RECOMMENDED_PARAMS,
    }


def main():
    print("=" * 60)
    print("AI Frontier Sample Generator - V0.2.5")
    print("=" * 60)
    print()

    # Check prerequisites
    print("Checking prerequisites...")
    ffmpeg_ok = check_ffmpeg()
    server_ok = check_server()
    print()

    if not server_ok:
        print("ERROR: API server is not running.")
        print("Please start the server and try again.")
        sys.exit(1)

    if not ffmpeg_ok:
        print("WARNING: FFmpeg not found. Video generation may fail.")
        print("Continuing anyway... (FFmpeg is required for actual video output)")
        print()

    # Show what we're going to do
    print("Sample Configuration:")
    print(f"  Test Case:    {TEST_CASE_ID}")
    print(f"  Method:       {METHOD_ID}")
    print(f"  Title:        {EXPERIMENT_TITLE}")
    print()
    print("Recommended Parameters:")
    for k, v in RECOMMENDED_PARAMS.items():
        print(f"  {k}: {v}")
    print()

    # Build request
    request = build_sample_request()
    print(f"Creating experiment via {API_BASE}/experiments...")
    print()

    try:
        resp = requests.post(
            f"{API_BASE}/experiments",
            json=request,
            timeout=120,  # Allow up to 2 min for video generation
        )

        if resp.status_code == 200:
            data = resp.json()
            experiment = data.get("experiment", {})
            result = data.get("result", {})

            print("=" * 60)
            print("SUCCESS")
            print("=" * 60)
            print()
            print(f"Experiment ID:  {experiment.get('id', 'N/A')}")
            print(f"Status:        {experiment.get('status', 'N/A')}")
            print(f"Elapsed:       {experiment.get('elapsedMs', 'N/A')}ms")
            print()

            assets = result.get("assets", {})
            print("Output URLs:")
            print(f"  Video URL:    {result.get('videoUrl', 'N/A')}")
            print(f"  Cover URL:    {result.get('coverUrl', 'N/A')}")
            print()

            # Try to find manifest URL from production steps
            production_steps = result.get("productionSteps", [])
            manifest_url = "N/A"
            for step in production_steps:
                if step.get("name") == "Generate Conclusion":
                    for art in step.get("artifacts", []):
                        if art.get("type") == "manifest":
                            manifest_url = art.get("payload", {}).get("manifestUrl", "N/A")
                            break

            print("Manifest URL:")
            print(f"  {manifest_url}")
            print()

            # Show runtime path
            exp_id = experiment.get("id", "")
            if exp_id:
                # Reconstruct runtime path
                print("Runtime Directory:")
                print(f"  (Check server logs for exact path)")
                print(f"  Experiment: {exp_id}")
                print()

            print("Next Steps:")
            print("  1. View experiment detail page")
            print("  2. Review generated video")
            print("  3. Complete human evaluation (评分)")
            print("  4. Check template review suggestions")
            print()

            # Summary of render params used
            render_params = assets.get("renderParams", {})
            if render_params:
                print("Render Parameters Used:")
                for k, v in render_params.items():
                    print(f"  {k}: {v}")
            print()

            return 0

        else:
            print(f"ERROR: HTTP {resp.status_code}")
            try:
                error_detail = resp.json().get("detail", resp.text)
                print(f"  {error_detail}")
            except Exception:
                print(f"  {resp.text[:200]}")
            return 1

    except requests.exceptions.Timeout:
        print("ERROR: Request timed out.")
        print("  The server may be overloaded or FFmpeg took too long.")
        print("  Check server logs for progress.")
        return 1
    except requests.exceptions.ConnectionError:
        print("ERROR: Connection to server lost.")
        print("  Please check if the server is still running.")
        return 1
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
