"""
speaker/main.py

Speaker identification app for modular pipeline. This script loads diarization results and audio, computes speaker embeddings using pyannote.audio, compares to known embeddings (.pt file), and outputs labeled diarization results. Requires Python 3.8, pyannote.audio==2.1.1, and torch.
"""

import os
import torch
import json
import numpy as np
import soundfile as sf
from pyannote.audio import Inference
from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding

def load_known_embeddings(embeddings_path):
    return torch.load(embeddings_path)

def cosine_similarity(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    return np.dot(a, b)

def extract_audio_segment(audio_path, start, end):
    data, sr = sf.read(audio_path)
    start_sample = int(start * sr)
    end_sample = int(end * sr)
    return data[start_sample:end_sample], sr

def identify_speakers(audio_path, diarization_path, embeddings_path, output_path, threshold=0.75):
    # Load diarization segments
    with open(diarization_path, 'r') as f:
        diarization = json.load(f)["segments"]
    # Load known speaker embeddings
    known_embeddings = load_known_embeddings(embeddings_path)
    # Assume known_embeddings is a dict: {"Speaker X": embedding_vector}
    target_emb = known_embeddings["Speaker X"]
    # Initialize pyannote speaker embedding model
    model = PretrainedSpeakerEmbedding(
        "speechbrain/spkrec-ecapa-voxceleb",
        device="cuda" if torch.cuda.is_available() else "cpu"
    )
    inference = Inference(model, window="whole")
    # For each segment, compute embedding and compare to known
    for seg in diarization:
        start, end = seg["start"], seg["end"]
        segment_audio, sr = extract_audio_segment(audio_path, start, end)
        # Save segment to temp file for inference
        with sf.SoundFile("_tmp.wav", 'w', sr, segment_audio.shape[1] if len(segment_audio.shape) > 1 else 1) as f:
            f.write(segment_audio)
        emb = inference("_tmp.wav")
        sim = cosine_similarity(emb, target_emb)
        # If match, label as 'Speaker X', else keep diarization speaker label
        if sim >= threshold:
            seg["speaker_label"] = "Speaker X"
        else:
            seg["speaker_label"] = seg["speaker"]  # Always keep diarization label for non-matches
        os.remove("_tmp.wav")
    # Save labeled diarization
    with open(output_path, 'w') as f:
        json.dump({"segments": diarization}, f, indent=2)

if __name__ == "__main__":
    # Example usage: python main.py audio.wav diarization.json embeddings.pt output.json
    import sys
    if len(sys.argv) != 5:
        print("Usage: python main.py <audio.wav> <diarization.json> <embeddings.pt> <output.json>")
        exit(1)
    identify_speakers(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
