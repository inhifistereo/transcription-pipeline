import ffmpeg
import asyncio

async def extract_audio_to_wav(video_path, wav_path):
    (
        ffmpeg
        .input(video_path)
        .output(wav_path, acodec='pcm_s16le', ac=1, ar='16k')
        .overwrite_output()
        .run(quiet=True)
    )
