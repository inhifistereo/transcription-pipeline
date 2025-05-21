import yt_dlp
import logging
from typing import List
import json
from utils.azure_blob import download_blob_async
import tempfile

async def fetch_video_ids(playlist_url: str) -> List[str]:
    """Fetch video IDs from a YouTube playlist using yt-dlp."""
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

async def get_input_from_blob(container: str, blob_name: str) -> str:
    """Download a blob and return its contents as a string."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        await download_blob_async(container, blob_name, tmp.name)
        tmp.seek(0)
        return tmp.read().decode()

async def main():
    import sys, asyncio
    logging.basicConfig(level=logging.INFO)
    # Accept input type and value (or blob location)
    if len(sys.argv) == 2:
        # Direct input (playlist URL, video ID, or JSON list)
        input_arg = sys.argv[1]
    elif len(sys.argv) == 4 and sys.argv[1] == '--blob':
        # Read input from blob
        container = sys.argv[2]
        blob_name = sys.argv[3]
        input_arg = await get_input_from_blob(container, blob_name)
    else:
        print("Usage: fetch_videos.py <playlist_url|video_id|[\"id1\",...] > OR fetch_videos.py --blob <container> <blob_name>")
        sys.exit(1)

    # Try to parse as JSON list
    try:
        video_ids = json.loads(input_arg)
        if isinstance(video_ids, list):
            print(video_ids)
            return
    except Exception:
        pass

    # Try to parse as comma-separated list
    if ',' in input_arg and not input_arg.strip().startswith('http'):
        video_ids = [v.strip() for v in input_arg.split(',') if v.strip()]
        print(video_ids)
        return

    # If it's a playlist URL
    if 'playlist' in input_arg:
        ids = await fetch_video_ids(input_arg)
        print(ids)
    else:
        # Assume single video ID or URL
        if 'youtube.com' in input_arg and 'v=' in input_arg:
            vid = input_arg.split('v=')[-1]
        else:
            vid = input_arg
        print([vid])

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
