"""
Speech-to-Text service for voice message transcription
"""
import httpx
from typing import Optional
from loguru import logger

from .config import settings


class SpeechToTextService:
    """Speech-to-Text service wrapper"""

    async def transcribe_audio_url(self, audio_url: str) -> Optional[str]:
        """
        Transcribe audio from URL

        Args:
            audio_url: URL to audio file

        Returns:
            Transcribed text or None if failed
        """
        try:
            if settings.SPEECH_TO_TEXT_PROVIDER == "whisper" and settings.OPENAI_API_KEY:
                return await self._transcribe_whisper(audio_url)
            else:
                logger.warning(f"Speech-to-text provider not configured: {settings.SPEECH_TO_TEXT_PROVIDER}")
                return None
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
            return None

    async def _transcribe_whisper(self, audio_url: str) -> Optional[str]:
        """Transcribe using OpenAI Whisper"""
        try:
            # Download audio file
            async with httpx.AsyncClient() as client:
                audio_response = await client.get(audio_url)
                audio_data = audio_response.content

            # Call Whisper API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    files={"file": ("audio.ogg", audio_data, "audio/ogg")},
                    data={"model": "whisper-1"}
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("text", "")
                else:
                    logger.error(f"Whisper API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return None


# Global speech-to-text service instance
speech_to_text_service = SpeechToTextService()
