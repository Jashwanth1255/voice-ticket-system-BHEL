import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel

# Recording settings
duration = 5  # seconds
sample_rate = 16000

print("Speak now...")
audio = sd.rec(
    int(duration * sample_rate),
    samplerate=sample_rate,
    channels=1,
    dtype="int16"
)
sd.wait()

write("audio.wav", sample_rate, audio)
print("Audio saved as audio.wav")

print("Loading Whisper model...")
model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

print("Transcribing...")
segments, info = model.transcribe("audio.wav")

print(f"Detected language: {info.language}")

print("\nTranscript:")
for segment in segments:
    print(segment.text)