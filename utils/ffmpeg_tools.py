import ffmpeg
import asyncio
import logging

async def extract_audio_to_wav(video_path: str, wav_path: str) -> str:
    """Extract mono WAV audio from video using ffmpeg."""
    logging.info(f"Extracting audio from {video_path} to {wav_path}")
    (
        ffmpeg
        .input(video_path)
        .output(wav_path, ac=1, ar='16k', format='wav')
        .overwrite_output()
        .run(quiet=True)
    )
    return wav_path
