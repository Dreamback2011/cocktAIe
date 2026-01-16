import os
from openai import OpenAI
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class VoiceService:
    """Whisper API语音转文字服务"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY环境变量未设置")
        self.client = OpenAI(api_key=api_key)
    
    async def transcribe_audio(
        self,
        audio_file_path: str,
        language: Optional[str] = "zh"
    ) -> str:
        """
        将音频文件转换为文字
        
        Args:
            audio_file_path: 音频文件路径
            language: 语言代码（默认中文）
        
        Returns:
            转录的文字内容
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="text"
                )
                return transcript if isinstance(transcript, str) else transcript.text
        except Exception as e:
            logger.error(f"语音转文字失败: {str(e)}")
            raise Exception(f"语音转文字失败: {str(e)}")
    
    def transcribe_audio_sync(
        self,
        audio_file_path: str,
        language: Optional[str] = "zh"
    ) -> str:
        """同步版本的语音转文字"""
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="text"
                )
                return transcript if isinstance(transcript, str) else transcript.text
        except Exception as e:
            logger.error(f"语音转文字失败: {str(e)}")
            raise Exception(f"语音转文字失败: {str(e)}")


# 全局服务实例
_voice_service_instance: Optional[VoiceService] = None


def get_voice_service() -> VoiceService:
    """获取全局语音服务实例"""
    global _voice_service_instance
    if _voice_service_instance is None:
        _voice_service_instance = VoiceService()
    return _voice_service_instance
