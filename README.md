# Modular YouTube Playlist Transcription Pipeline with Azure Blob Storage

This project provides a modular, async-friendly Python pipeline to:
- List video IDs from a YouTube playlist (`fetch_videos.py`)
- Download videos and extract mono WAV audio (`download_and_prepare.py`)
- Upload/download files to/from Azure Blob Storage
- Transcribe audio with Whisper (`transcribe_with_whisper.py`)
- Save transcripts with timestamps as JSON in Blob Storage
- Orchestrate the pipeline for a single video (`run_pipeline.py`)

## Project Structure

- `fetch_videos.py` — List video IDs from a playlist using yt-dlp
- `download_and_prepare.py` — Download video, extract audio, upload both to Azure Blob
- `transcribe_with_whisper.py` — Download audio, transcribe with Whisper, upload transcript
- `run_pipeline.py` — Orchestrate the above for a single video
- `utils/` — Azure Blob helpers, FFmpeg tools, Whisper wrappers
- `requirements.txt` — Dependencies
- `Dockerfile` — For Azure Container Apps deployment

## Azure Blob Containers
- `videos` — for .mp4 files
- `audio` — for .wav files
- `transcripts` — for .json Whisper output
- `trigger` — **(for Azure Function Blob Trigger integration)**
  - This container is monitored by the Azure Function.
  - When a new blob is added, the function is triggered to start processing.
- `videos-processed` — for processed .mp4 files (videos are moved here after audio extraction)

## Environment Variables
Set the following environment variables (e.g., in your deployment or `.env`):
- `AZURE_STORAGE_ACCOUNT_NAME` — your Azure Storage account name
- `AZURE_STORAGE_ACCOUNT_KEY` — your Azure Storage account key
- `AZURE_BLOB_VIDEOS_CONTAINER` — container for videos (default: `videos`)
- `AZURE_BLOB_AUDIO_CONTAINER` — container for audio (default: `audio`)
- `AZURE_BLOB_TRANSCRIPTS_CONTAINER` — container for transcripts (default: `transcripts`)
- `AZURE_BLOB_PROCESSED_VIDEOS_CONTAINER` — container for processed videos (**required**, e.g., `videos-processed`)
- `AZURE_SUBSCRIPTION_ID` — your Azure subscription ID **(for Azure Function)**
- `AZURE_RESOURCE_GROUP` — your Azure resource group **(for Azure Function)**
- `AZURE_CONTAINER_APP_NAME` — your Azure Container App name **(for Azure Function)**
- `ACA_CONTAINER_IMAGE` — your Azure Container image **(for Azure Function)**
- `ACA_ENVIRONMENT` — your Azure Container App environment **(for Azure Function)**

## Usage
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Download and upload videos to Azure Blob Storage:
   ```bash
   python -c "import asyncio; from download_and_prepare import download_and_upload_video; asyncio.run(download_and_upload_video('<video_id>'))"
   ```
   This will place the video in the `videos` container.

3. Run the pipeline to process all videos already in the `videos` container:
   ```bash
   python run_pipeline.py
   ```
   This will extract audio, upload to `audio`, move processed videos to `videos-processed`, and transcribe audio.

## Docker
Build and run with Docker:
```bash
docker build -t yt-whisper-pipeline .
docker run --env-file .env yt-whisper-pipeline
```

## Event-Driven Processing with Azure Function

You can automate the pipeline using an Azure Function with a Blob Trigger:
- When a new blob is added to the `trigger` container, the Azure Function will start an Azure Container App job to process the input.
- The function uses managed identity for secure authentication and launches the container with the blob details as arguments.

**Example Azure Function logic:**
- See `azure_function_blob_trigger.py` in this repo for a sample implementation.
- Required environment variables for the function:
  - `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP`, `AZURE_CONTAINER_APP_NAME`, `ACA_CONTAINER_IMAGE`, `ACA_ENVIRONMENT`
- The function will run your container with:
  ```bash
  python fetch_videos.py --blob <container> <blob_name>
  ```

**Typical workflow:**
1. Upload a file (playlist URL, video IDs, etc.) to the `trigger` container in Azure Blob Storage.
2. The Azure Function is triggered and starts the pipeline in Azure Container Apps.
3. The pipeline processes all videos as described above.

## Notes
- All operations are async where possible
- Logging is included
- No unnecessary disk writes; files are streamed to/from Azure Blob
- Requires ffmpeg installed in the environment

---

## Changes
- The pipeline now requires the `videos-processed` container for processed videos.
- `run_pipeline.py` no longer downloads videos; it processes those already in the `videos` container.
- Download/upload and audio extraction/upload are now separate steps.
