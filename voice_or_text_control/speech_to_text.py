import sounddevice as sd
import numpy as np
import whisper

def record_and_transcribe():
    duration = int(input("Enter length of audio recording: ")) # seconds
    samplerate = 16000  # Whisper expects 16000 Hz
    # Record audio
    print("Recording...")
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    print("Recording complete.")

    # Convert int16 PCM to float32 normalized between -1.0 and 1.0
    recording = recording.flatten().astype(np.float32) / 32768.0

    # Load Whisper model
    print("Loading Whisper model...")
    model = whisper.load_model("base")  # You can use "tiny", "small", etc. too

    # Transcribe the audio
    print("Transcribing...")
    transcript = model.transcribe(recording)

    # Output the result
    print("Transcription:", transcript["text"])
    return transcript["text"]