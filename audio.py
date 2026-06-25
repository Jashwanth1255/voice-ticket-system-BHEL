from scipy.io.wavfile import read

rate, data = read("recorded.wav")

print("Sample Rate:", rate)
print("Audio Shape:", data.shape)
print("Max Value:", max(data))