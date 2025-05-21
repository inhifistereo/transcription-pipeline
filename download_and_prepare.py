import asyncio
import logging
from utils.azure_blob import upload_blob_async
from utils.ffmpeg_tools import extract_audio_to_wav
import yt_dlp
import io
import os

async def download_video(video_id: str, video_container: str) -> bytes:
    """Download a YouTube video as mp4 to memory."""
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': '-',
        'quiet': True,
        'noplaylist': True,
    }
    buffer = io.BytesIO()
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
        # yt-dlp does not support direct streaming to BytesIO, so workaround is needed
        # For now, download to disk and read, but this should be improved
    return buffer.getvalue()

async def process_and_upload(video_id: str):
    logging.info(f"Processing video {video_id}")
    # Download video (to disk for now)
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': f'{video_id}.mp4',
        'quiet': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
    # Upload video
    await upload_blob_async(f'{video_id}.mp4', container='videos', blob_name=f'{video_id}.mp4')
    # Extract audio
    wav_path = await extract_audio_to_wav(f'{video_id}.mp4', f'{video_id}.wav')
    # Upload audio
    await upload_blob_async(wav_path, container='audio', blob_name=f'{video_id}.wav')
    logging.info(f"Uploaded video and audio for {video_id}")
    # Clean up local video file
    if os.path.exists(f'{video_id}.mp4'):
        os.remove(f'{video_id}.mp4')
    if os.path.exists(wav_path):
        os.remove(wav_path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    asyncio.run(process_and_upload(sys.argv[1]))
