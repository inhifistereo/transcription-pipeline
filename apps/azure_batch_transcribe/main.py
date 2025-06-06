import os
from shared.utils.blob import download_blob, upload_blob
from shared.utils.logging import setup_logging
# Azure Speech SDK imports...

def submit_batch_job(audio_uri):
    # Submit to Azure Speech Batch API
    pass

def poll_job(job_id):
    # Poll for completion
    pass

def download_transcript(job_id, out_path):
    # Download transcript
    pass

def main():
    setup_logging()
    # Get audio URI from env/blob
    # Submit, poll, download, upload transcript

if __name__ == '__main__':
    main()
