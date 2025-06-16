"""
transcribe_with_whisper.py

This script downloads audio chunk files from Azure Blob Storage, transcribes each chunk using Whisper, performs speaker diarization using pyannote.audio, aligns speaker segments with transcript segments, and uploads both a merged transcript (JSON), diarization (JSON), and a readable speaker script (TXT) to Azure Blob Storage. It is designed for use in a modular, async pipeline for YouTube playlist transcription and speaker recognition, compatible with Azure Container Apps.

Dependencies:
- whisper
- pyannote.audio
- torch
- ffmpeg-python
- soundfile
- azure-storage-blob
- aiohttp

Purpose:
- To generate a single transcript file per meeting/video, with speaker labels and a human-readable speaker script, using async and temp file best practices.
"""

import asyncio
import logging
import os
import tempfile
import json
from utils.azure_blob import download_blob_async, upload_blob_async, list_blobs_async
from utils.whisper_wrapper import transcribe_audio
from pyannote.audio import Pipeline

# No chunking logic here; download_and_prepare.py handles chunking.

def diarize_audio(audio_path):
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    if not hf_token:
        raise RuntimeError("HUGGINGFACE_TOKEN environment variable not set. Please set it to your Hugging Face access token.")
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=hf_token)
    diarization = pipeline(audio_path)
    segments = []
    for segment, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({
            "start": segment.start,
            "end": segment.end,
            "speaker": speaker
        })
    return segments

async def transcribe_and_upload(video_id: str, enable_diarization: bool = True):
    import re
    audio_container = os.getenv('AZURE_BLOB_AUDIO_CONTAINER', 'audio')
    
    # Filter chunks for this specific video
    all_blobs = await list_blobs_async(audio_container)
    chunk_blobs = [blob for blob in all_blobs if blob.startswith(f"{video_id}_chunk_")]
    
    logging.info(f"Processing video: {video_id}")
    logging.info(f"Found {len(chunk_blobs)} audio chunks: {chunk_blobs}")
    
    if not chunk_blobs:
        logging.info(f"No audio chunks found for video {video_id}. Skipping transcription.")
        return
    
    temp_files = []
    all_segments = []
    diarization_segments = []
    speaker_script_path = None
    
    try:
        # Sort chunks by number
        def chunk_sort_key(x):
            match = re.search(r"chunk_(\d+)", x)
            return int(match.group(1)) if match else float('inf')
        
        sorted_chunks = sorted(chunk_blobs, key=chunk_sort_key)
        logging.info(f"Processing chunks in order: {sorted_chunks}")
        
        # Process each chunk for transcription
        for chunk_blob in sorted_chunks:
            chunk_path = f"/tmp/{chunk_blob}"
            temp_files.append(chunk_path)
            
            logging.info(f"Downloading and transcribing {chunk_blob}")
            await download_blob_async(audio_container, chunk_blob, chunk_path)
            transcript = await transcribe_audio(chunk_path)
            result = json.loads(transcript)
            all_segments.extend(result.get('segments', []))
            logging.info(f"  Got {len(result.get('segments', []))} segments")
        
        # Always upload basic transcript first
        transcript_json_path = f"/tmp/{video_id}_transcript.json"
        with open(transcript_json_path, 'w') as f:
            json.dump({"segments": all_segments}, f, indent=2)
        await upload_blob_async(transcript_json_path, container='transcripts', blob_name=f'{video_id}_transcript.json')
        logging.info(f"Transcript JSON uploaded for {video_id}")
        temp_files.append(transcript_json_path)
        
        # Try speaker diarization if enabled
        if enable_diarization and sorted_chunks:
            try:
                logging.info(f"Starting speaker diarization for {video_id}")
                diarization_audio_path = f"/tmp/{sorted_chunks[0]}"
                diarization_segments = diarize_audio(diarization_audio_path)

                # Write diarization JSON
                diarization_json_path = f"/tmp/{video_id}_diarization.json"
                with open(diarization_json_path, 'w') as f:
                    json.dump({"segments": diarization_segments}, f, indent=2)
                await upload_blob_async(diarization_json_path, container='transcripts', blob_name=f'{video_id}_diarization.json')
                logging.info(f"Diarization JSON uploaded for {video_id}")
                temp_files.append(diarization_json_path)

                # Generate enhanced speaker script with diarization
                speaker_script_path = f"/tmp/{video_id}_speaker_script.txt"
                with open(speaker_script_path, 'w') as f:
                    # Align transcript segments with speaker segments
                    for seg in all_segments:
                        # Find matching speaker for this time segment
                        speaker = "Unknown"
                        seg_start = seg.get('start', 0)
                        for diar_seg in diarization_segments:
                            if diar_seg['start'] <= seg_start <= diar_seg['end']:
                                speaker = diar_seg['speaker']
                                break
                        f.write(f"{speaker} - {seg['start']:.2f} to {seg['end']:.2f}: {seg['text'].strip()}\n\n")
                await upload_blob_async(speaker_script_path, container='transcripts', blob_name=f'{video_id}_speaker_script.txt')
                logging.info(f"Speaker script with diarization uploaded for {video_id}")

            except Exception as e:
                logging.error(f"Speaker diarization failed for {video_id}: {e}")
                logging.info(f"Continuing with basic transcript only for {video_id}")

                # Generate basic speaker script with sequential speaker labels
                speaker_script_path = f"/tmp/{video_id}_speaker_script.txt"
                speaker_counter = 1
                with open(speaker_script_path, 'w') as f:
                    for seg in all_segments:
                        speaker_label = f"Speaker {speaker_counter}"
                        f.write(f"{speaker_label} - {seg['start']:.2f} to {seg['end']:.2f}: {seg['text'].strip()}\n\n")
                        speaker_counter += 1
                await upload_blob_async(speaker_script_path, container='transcripts', blob_name=f'{video_id}_speaker_script.txt')
                logging.info(f"Basic speaker script with labels uploaded for {video_id}")
        else:
            # Generate basic speaker script with sequential speaker labels
            speaker_script_path = f"/tmp/{video_id}_speaker_script.txt"
            speaker_counter = 1
            with open(speaker_script_path, 'w') as f:
                for seg in all_segments:
                    speaker_label = f"Speaker {speaker_counter}"
                    f.write(f"{speaker_label} - {seg['start']:.2f} to {seg['end']:.2f}: {seg['text'].strip()}\n\n")
                    speaker_counter += 1
            await upload_blob_async(speaker_script_path, container='transcripts', blob_name=f'{video_id}_speaker_script.txt')
            logging.info(f"Basic speaker script with labels uploaded for {video_id}")
            
    except Exception as e:
        logging.error(f"Failed to process transcription for {video_id}: {e}")
        raise
    finally:
        # Clean up temp files
        all_temp_files = temp_files + ([speaker_script_path] if speaker_script_path else [])
        for path in all_temp_files:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
                    logging.debug(f"Cleaned up temp file: {path}")
            except Exception as e:
                logging.warning(f"Failed to remove temp file {path}: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    video_id = sys.argv[1] if len(sys.argv) > 1 else "test"
    enable_diarization = len(sys.argv) < 3 or sys.argv[2].lower() != "false"
    asyncio.run(transcribe_and_upload(video_id, enable_diarization))
