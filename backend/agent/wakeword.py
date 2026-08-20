"""
Wake Word Detection Engine ("Hey Chaitanya").
Handles background acoustic detection, wake word state tracking, 
and audio stream processing.
"""

import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("agent.wakeword")

_WAKE_WORD_ACTIVE = True
_SENSITIVITY = 0.75  # 0.0 to 1.0
_WAKE_PHRASES = ["hey chaitanya", "chaitanya", "ok chaitanya", "hello chaitanya", "aegis"]


def is_wake_word_phrase(transcription: str) -> bool:
    """Check if the transcribed audio text contains the wake word phrase."""
    if not transcription:
        return False
    text = transcription.lower().strip()
    return any(phrase in text for phrase in _WAKE_PHRASES)


def set_wake_word_enabled(enabled: bool) -> bool:
    global _WAKE_WORD_ACTIVE
    _WAKE_WORD_ACTIVE = enabled
    return _WAKE_WORD_ACTIVE


def get_wake_word_status() -> Dict[str, Any]:
    return {
        "enabled": _WAKE_WORD_ACTIVE,
        "sensitivity": _SENSITIVITY,
        "phrases": _WAKE_PHRASES,
        "status": "listening" if _WAKE_WORD_ACTIVE else "disabled"
    }


def process_wake_word_audio(audio_bytes: bytes) -> Dict[str, Any]:
    """
    Process incoming audio buffer from desktop microphone to detect wake word.
    """
    if not _WAKE_WORD_ACTIVE:
        return {"detected": False, "reason": "wake_word_disabled"}

    try:
        from .voice import process_speech_to_text
        text = process_speech_to_text(audio_bytes)
        detected = is_wake_word_phrase(text)

        return {
            "detected": detected,
            "transcription": text,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Wake word audio processing error: {e}")
        return {"detected": False, "error": str(e)}
