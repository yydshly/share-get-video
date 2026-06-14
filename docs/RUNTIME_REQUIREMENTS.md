# 运行时依赖要求

本文档说明 Video Capability Lab V0.3.5-dev 的所有运行时依赖。

## 必需依赖

### Python >= 3.10

```bash
python --version  # 需 >= 3.10
```

Python 依赖通过 pip 安装：

```bash
pip install -r requirements.txt
```

**注意**：`requirements.txt` 只声明 Python 包，不包含 FFmpeg / Node.js / Remotion。

### FFmpeg

FFmpeg 必须安装并可通过命令行调用。

```bash
ffmpeg -version
```

**用途**：
- `local_frame_compose` 路线：帧序列合成 MP4
- `tts_subtitle_compose` 路线：音视频字幕合成
- 所有涉及视频编码/解码的操作

**安装方式**（Windows）：

```powershell
# winget
winget install ffmpeg

# 或从 https://ffmpeg.org/download.html 下载并添加到 PATH
```

**安装方式**（macOS）：

```bash
brew install ffmpeg
```

**安装方式**（Linux）：

```bash
sudo apt install ffmpeg  # Ubuntu/Debian
sudo yum install ffmpeg   # CentOS/RHEL
```

### Node.js >= 20

```bash
node --version  # 需 >= 20.0.0
```

仅 `template_programmatic_render` 路线需要。

**用途**：运行 Remotion CLI 执行程序化视频渲染

**安装方式**：从 https://nodejs.org 下载或使用 nvm

## 可选依赖

### MiniMax API Key

**环境变量**：`MINIMAX_API_KEY`

**用途**：`tts_subtitle_compose` 路线的 MiniMax TTS 语音合成

**配置方式**：

```bash
# Windows
set MINIMAX_API_KEY=your_api_key_here

# Linux/macOS
export MINIMAX_API_KEY=your_api_key_here
```

或创建 `.env` 文件（项目根目录）：

```
MINIMAX_API_KEY=your_api_key_here
```

**影响**：
- 有 API Key：`tts_subtitle_compose` 路线状态为 `real`
- 无 API Key：`tts_subtitle_compose` 路线状态为 `not_configured`（adapter 会返回失败）

### Remotion Workspace

位于项目根目录 `remotion/` 子目录。

**用途**：`template_programmatic_render` 路线

**依赖项**：

```bash
cd remotion
npm install
```

**注意**：Remotion 渲染会下载 Chrome headless 浏览器（约 150MB）

## 路线与依赖关系

| 路线 | Python | FFmpeg | Node.js | MiniMax API |
|------|--------|--------|---------|-------------|
| `local_frame_compose` | ✅ | ✅ | ❌ | ❌ |
| `template_programmatic_render` | ✅ | ✅ | ✅ | ❌ |
| `hyperframes_html_render` | ✅ | ❌ | ❌ | ❌ |
| `tts_subtitle_compose` | ✅ | ✅ | ❌ | ✅ |
| `local_media_compose` | ✅ | ✅ | ❌ | ❌ |
| `ai_video_direct` | ❌ | ❌ | ❌ | ❌ |
| `ai_asset_then_compose` | ❌ | ❌ | ❌ | ❌ |
| `hybrid_pipeline` | ❌ | ❌ | ❌ | ❌ |

## 快速检查命令

```bash
# 检查所有依赖
python --version && echo "Python OK"
node --version && echo "Node.js OK"
ffmpeg -version && echo "FFmpeg OK"

# 检查 MiniMax API Key（可选）
echo $MINIMAX_API_KEY | grep -q . && echo "MINIMAX_API_KEY set" || echo "MINIMAX_API_KEY not set"
```

## 依赖缺失时的行为

| 依赖缺失 | 受影响路线 | 行为 |
|---------|-----------|------|
| FFmpeg | local_frame_compose, tts_subtitle_compose | 路线返回 `failed`，warning 提示 FFmpeg 不可用 |
| Node.js | template_programmatic_render | 路线返回 `failed`，warning 提示 Remotion 环境不可用 |
| MiniMax API Key | tts_subtitle_compose | 路线返回 `failed`，warning 提示 API Key 未配置 |

