import sys
from pathlib import Path
# Ensure project root is in sys.path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

import asyncio
import os
import logging
from utils.azure_blob import list_blobs_async, download_blob_async, upload_blob_async
from utils.ffmpeg_tools import extract_audio_to_wav
import tempfile

async def create_full_wavs_from_chunks(audio_container='audio', output_container=None):
    output_container = output_container or audio_container
    audio_blobs = await list_blobs_async(audio_container)
    video_ids = set(blob.split('_chunk_')[0] for blob in audio_blobs if '_chunk_' in blob)
    for video_id in video_ids:
        # Find all chunks for this video and sort by chunk number
        chunks = sorted([b for b in audio_blobs if b.startswith(video_id + '_chunk_')],
                        key=lambda x: int(x.split('_chunk_')[1].split('.')[0]))
        if not chunks:
            continue
        logging.info(f"Processing {video_id}: {len(chunks)} chunks")
        temp_chunk_paths = []
        try:
            # Download all chunks
            for chunk_blob in chunks:
                temp_path = tempfile.mktemp(suffix='.wav')
                await download_blob_async(audio_container, chunk_blob, temp_path)
                temp_chunk_paths.append(temp_path)
            # Concatenate using ffmpeg
            concat_list_path = tempfile.mktemp(suffix='.txt')
            with open(concat_list_path, 'w') as f:
                for path in temp_chunk_paths:
                    f.write(f"file '{path}'\n")
            full_wav_path = f"{video_id}_full.wav"
            import ffmpeg
            (
                ffmpeg
                .input(concat_list_path, format='concat', safe=0)
                .output(full_wav_path, acodec='pcm_s16le', ac=1, ar='16k')
                .overwrite_output()
                .run(quiet=True)
            )
            await upload_blob_async(full_wav_path, container=output_container, blob_name=full_wav_path)
            logging.info(f"Uploaded {full_wav_path} to {output_container}")
        finally:
            for f in temp_chunk_paths:
                if os.path.exists(f):
                    os.remove(f)
            if os.path.exists(concat_list_path):
                os.remove(concat_list_path)
            if os.path.exists(full_wav_path):
                os.remove(full_wav_path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(create_full_wavs_from_chunks())
