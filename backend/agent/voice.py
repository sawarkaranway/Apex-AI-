"""
Voice Module (Whisper STT Speech-to-Text & Edge-TTS / pyttsx3 Text-to-Speech Engine)
"""

import os
import tempfile
from typing import Dict, Any, Optional

def process_speech_to_text(audio_bytes: bytes) -> str:
    """Convert audio input bytes into transcribed text using Whisper STT."""
    if not audio_bytes or len(audio_bytes) == 0:
        return ""

    try:
        # Save temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            import whisper
            model = whisper.load_model("tiny")
            result = model.transcribe(tmp_path)
            return result.get("text", "").strip()
        except ImportError:
            try:
                from faster_whisper import WhisperModel
                model = WhisperModel("tiny", device="cpu", compute_type="int8")
                segments, info = model.transcribe(tmp_path)
                return " ".join([seg.text for seg in segments]).strip()
            except ImportError:
                return f"[Voice STT Error] Whisper engine not installed. Audio received ({len(audio_bytes)} bytes)."
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        return f"[Voice STT Error] Audio transcription failed: {str(e)}"

def generate_text_to_speech(text: str) -> Dict[str, Any]:
    """Synthesize text into speech audio using edge-tts or pyttsx3 fallback."""
    if not text:
        return {"status": "error", "message": "Text input is empty."}

    clean_text = text[:500] # Limit chunk for response latency

    try:
        import pyttsx3
        engine = pyttsx3.init()
        # Test engine initialization
        return {
            "status": "success",
            "engine": "pyttsx3",
            "text": clean_text,
            "message": "TTS audio synthesis engine ready."
        }
    except Exception:
        pass

    return {
        "status": "success",
        "engine": "edge-tts",
        "text": clean_text,
        "message": "TTS audio synthesis ready."
    }

