# Modular YouTube Audio Transcription & Speaker ID Pipeline (Azure ACA)

## Overview

This pipeline ingests YouTube videos, extracts and chunks audio, transcribes with Azure Speech Batch or Whisper, diarizes with pyannote.audio, identifies speakers, and merges results into human/machine-readable transcripts. Each step is a modular Azure Container App.

## Project Structure

```
apps/
  download_and_prepare/
    main.py
  whisper_transcribe/
    main.py
  # ...other modules
libs/
  azure_blob.py
  ffmpeg_tools.py
  whisper_wrapper.py
shared/
  utils/
  requirements/
docker/
  base/
  pyannote/
  transcriber/
infra/
.github/
README.md
```

## Pipeline Flow

1. **download_and_prepare**: Download YouTube video, extract audio, chunk, upload to Blob.
2. **whisper_transcribe**: Download audio chunks, transcribe with Whisper, diarize, upload transcript.
3. **(other modules as needed)**

## Services & Inputs/Outputs

| Service                        | Input Blob(s)         | Output Blob(s)         |
|--------------------------------|-----------------------|------------------------|
| download_and_prepare           | YouTube URL           | audio.wav, chunks/*.wav|
| whisper_transcribe             | chunks/*.wav          | transcript.json, speaker_script.txt |
| ...                            | ...                   | ...                    |

## Local Run

Each app can be run locally with Docker and appropriate env vars.

## Deployment

- Push to main triggers GitHub Actions: builds images, pushes to ACR, applies Terraform to deploy ACA.
- All secrets/credentials are managed via GitHub/Azure Key Vault.

## Credentials

- **Hugging Face**: `HUGGINGFACE_TOKEN`
- **Azure Speech**: `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`
- **Azure Blob**: `AZURE_STORAGE_ACCOUNT_NAME`, `AZURE_STORAGE_ACCOUNT_KEY`
- **ACR**: `ACR_NAME`

## Environment Variables

Each service expects its own set of env vars (see code and infra).

## How to Deploy

1. Set up Azure resources with Terraform in `infra/`.
2. Push to `main` branch to trigger CI/CD in `.github/workflows/deploy.yml`.
3. Each app is built, pushed to ACR, and deployed to ACA.

## How to Run Locally

- Build the relevant Docker image in `apps/<app_name>/`.
- Run with `docker run --env-file .env <image>`.

## Notes

- All code is modular and async where possible.
- Speaker diarization and readable speaker scripts are included.
- Requires ffmpeg installed in the environment.
- GPU is supported for Whisper and diarization if available.

---
