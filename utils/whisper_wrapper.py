import whisper
import json
import logging

async def transcribe_audio(audio_path: str) -> str:
    logging.info(f"Transcribing {audio_path} with Whisper")
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, word_timestamps=True)
    return json.dumps(result, indent=2)
