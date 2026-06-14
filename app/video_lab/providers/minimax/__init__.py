"""
MiniMax TTS Provider
V0.3.3: MiniMax TTS client for voiceover generation
"""

from app.video_lab.providers.minimax.tts_client import MiniMaxTTSClient, MiniMaxTTSError
from app.video_lab.providers.minimax.chat_client import MiniMaxChatClient
from app.video_lab.providers.minimax.image_client import MiniMaxImageClient

__all__ = ["MiniMaxTTSClient", "MiniMaxTTSError", "MiniMaxChatClient", "MiniMaxImageClient"]
