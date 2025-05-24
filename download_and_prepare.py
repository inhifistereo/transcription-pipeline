import asyncio
import logging
from utils.azure_blob import upload_blob_async, download_blob_async
from utils.ffmpeg_tools import extract_audio_to_wav
import yt_dlp
import os

async def download_and_upload_video(video_id: str, videos_container: str = 'videos'):
    """Download a YouTube video and upload to Azure Blob Storage."""
    logging.info(f"Downloading video {video_id}")
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': f'{video_id}.mp4',
        'quiet': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
    await upload_blob_async(f'{video_id}.mp4', container=videos_container, blob_name=f'{video_id}.mp4')
    logging.info(f"Uploaded {video_id}.mp4 to {videos_container}")
    if os.path.exists(f'{video_id}.mp4'):
        os.remove(f'{video_id}.mp4')

async def extract_audio_from_blob_and_upload(video_blob_name: str, videos_container: str = 'videos', audio_container: str = 'audio', processed_container: str = 'videos-processed'):
    """Download video from blob, extract audio, upload audio, move video to processed container."""
    import tempfile
    video_id = os.path.splitext(os.path.basename(video_blob_name))[0]
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_video:
        tmp_video_path = tmp_video.name
    await download_blob_async(videos_container, video_blob_name, tmp_video_path)
    wav_path = await extract_audio_to_wav(tmp_video_path, f'{video_id}.wav')
    await upload_blob_async(wav_path, container=audio_container, blob_name=f'{video_id}.wav')
    logging.info(f"Uploaded audio {video_id}.wav to {audio_container}")
    # Move video to processed container
    from azure.storage.blob.aio import BlobServiceClient
    import os
    AZURE_STORAGE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    AZURE_STORAGE_ACCOUNT_KEY = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    blob_service_client = BlobServiceClient(
        f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
        credential=AZURE_STORAGE_ACCOUNT_KEY
    )
    src_client = blob_service_client.get_blob_client(videos_container, video_blob_name)
    dest_client = blob_service_client.get_blob_client(processed_container, video_blob_name)
    src_url = src_client.url
    await dest_client.start_copy_from_url(src_url)
    await src_client.delete_blob()
    logging.info(f"Moved {video_blob_name} to {processed_container}")
    # Clean up
    if os.path.exists(tmp_video_path):
        os.remove(tmp_video_path)
    if os.path.exists(wav_path):
        os.remove(wav_path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    asyncio.run(download_and_upload_video(sys.argv[1]))
