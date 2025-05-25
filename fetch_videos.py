import yt_dlp
import logging
import sys
import asyncio
from utils.azure_blob import upload_blob_async
import os

def parse_input(input_arg):
    import json
    # Try JSON list
    try:
        video_ids = json.loads(input_arg)
        if isinstance(video_ids, list):
            return video_ids
    except Exception:
        pass
    # Try comma-separated
    if ',' in input_arg and not input_arg.strip().startswith('http'):
        return [v.strip() for v in input_arg.split(',') if v.strip()]
    # Playlist URL
    if 'playlist' in input_arg:
        return None  # handled below
    # Single video
    if 'youtube.com' in input_arg and 'v=' in input_arg:
        return [input_arg.split('v=')[-1]]
    return [input_arg]

async def fetch_video_ids(playlist_url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
        'forcejson': True,
    }
    video_ids = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
        for entry in info.get('entries', []):
            video_ids.append(entry['id'])
    logging.info(f"Fetched {len(video_ids)} video IDs from playlist.")
    return video_ids

async def download_and_upload_video(video_id: str, videos_container: str = 'videos'):
    logging.info(f"Downloading video {video_id}")
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # ensure both video and audio are downloaded
        'outtmpl': f'{video_id}.mp4',
        'quiet': True,
        'noplaylist': True,
        'merge_output_format': 'mp4',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
    await upload_blob_async(f'{video_id}.mp4', container=videos_container, blob_name=f'{video_id}.mp4')
    logging.info(f"Uploaded {video_id}.mp4 to {videos_container}")
    if os.path.exists(f'{video_id}.mp4'):
        os.remove(f'{video_id}.mp4')

async def main():
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) == 2:
        input_arg = sys.argv[1]
    else:
        print("Usage: fetch_videos.py <playlist_url|video_id|[\"id1\",...] >")
        sys.exit(1)
    ids = parse_input(input_arg)
    if ids is None:
        # Playlist URL
        ids = await fetch_video_ids(input_arg)
    for vid in ids:
        await download_and_upload_video(vid)

if __name__ == "__main__":
    asyncio.run(main())
