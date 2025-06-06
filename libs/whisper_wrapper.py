# Moved from utils/whisper_wrapper.py

import whisper
import json
import asyncio

async def transcribe_audio(audio_path: str, model_size: str = 'base') -> str:
    model = whisper.load_model(model_size)
    result = await asyncio.to_thread(model.transcribe, audio_path)
    return json.dumps(result)
