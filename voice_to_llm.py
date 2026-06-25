import requests
from faster_whisper import WhisperModel
import sounddevice as sd
from scipy.io.wavfile import write
import os
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------
# CONFIG
# ---------------------------
# Put the other Windows device's LM Studio API here.
# Example for a LAN-hosted OpenAI-compatible LM Studio server:
#   set LLM_API_URL=http://10.5.131.123:1234/v1/chat/completions
LLM_API_URL = os.getenv(
    "LLM_API_URL",
    "http://10.5.65.131:1234/v1/chat/completions"
)
LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "qwen3.5-9b-sft-claude-opus-reasoning-unsloth"
)
# LLM_MODEL = "it-support-mistral-7b-expert"
# qwen3.5-9b-sft-claude-opus-reasoning-unsloth
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium")
# ---------------------------
# 1. RECORD AUDIO
# ---------------------------
duration = 8
sample_rate = 16000
WHISPER_INITIAL_PROMPT = (
    "This is an IT support complaint. The only expected spoken languages are "
    "English, Telugu, and Hindi. The speaker may use one of these languages or a "
    "code-switched mix where IT terminology remains in English. Do not interpret "
    "the audio as any other language. Transcribe the spoken words exactly. Do not "
    "translate. Preserve English technical terms, product names, acronyms, and "
    "error messages as English."
)
WHISPER_HOTWORDS = (
    "laptop desktop printer scanner monitor keyboard mouse Wi-Fi LAN VPN IP DNS "
    "router switch firewall server database Oracle SQL password login logout "
    "username account MFA OTP CPU RAM hard disk SSD software application app "
    "browser email Outlook Teams ticket incident error issue crash install update "
    "license network internet intranet portal website"
)

print("Speak now...")
audio = sd.rec(int(duration * sample_rate),
               samplerate=sample_rate,
               channels=1,
               dtype="int16")

sd.wait()
write("audio.wav", sample_rate, audio)
print("Audio saved")

# ---------------------------
# 2. SPEECH TO TEXT
# ---------------------------
print(f"\nUsing Whisper model: {WHISPER_MODEL}")
model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")

segments, info = model.transcribe(
    "audio.wav",
    language=None,
    task="transcribe",
    beam_size=5,
    multilingual=True,
    vad_filter=True,
    condition_on_previous_text=True,
    initial_prompt=WHISPER_INITIAL_PROMPT,
    hotwords=WHISPER_HOTWORDS,
    language_detection_threshold=0.25,
    language_detection_segments=3,
)

text = " ".join([seg.text for seg in segments])

if getattr(info, "language", None):
    probability = getattr(info, "language_probability", None)
    if probability is not None:
        print(f"\nPrimary detected language: {info.language} ({probability:.2%})")
    else:
        print(f"\nPrimary detected language: {info.language}")

print("\nTranscript:", text)

# ---------------------------
# 3. SEND TO REMOTE LOCAL MODEL API
# ---------------------------
payload = {
    "model": LLM_MODEL,
    "messages": [
        {
            "role": "system",
            "content": """
You are an IT Operations & Maintenance (IT O&M) ticketing assistant.

You are running as a local instruction-following model through LM Studio.
Follow these instructions exactly.

Your job:
- Convert user speech text into structured IT incident tickets.
- Focus only on IT infrastructure, software, hardware, network, and system issues.
- Classify the category from the user's exact complaint. Do not default to Network.
- If the complaint mentions a physical device, machine, peripheral, laptop, desktop, monitor, keyboard, mouse, printer, scanner, CPU, RAM, hard disk, battery, charger, cable, port, fan, overheating, power issue, broken device, or device not turning on, use category "Hardware".
- Use "Network" only for connectivity, internet, Wi-Fi, LAN, VPN, IP, DNS, router, switch, firewall, packet loss, latency, or unreachable network services.
- Use "Software" for application, OS, install, update, crash, license, browser, or login app errors that are not access permission issues.
- Use "Access" for password, account lock, permission, role, MFA, or authorization issues.
- Use "Server" for server down, service stopped, CPU/memory/disk on a server, deployment, or hosting issues.
- Use "Database" for SQL, Oracle, table, query, backup, replication, or database connection issues.
- Use "Security" for malware, phishing, suspicious activity, data breach, or policy violations.

Return output in STRICT JSON format:

{
  "category": "",
  "subcategory": "",
  "priority": "",
  "issue": "",
  "affected_system": "",
  "location": "",
  "suggested_action": ""
}

Rules:
- category must be one of: Network, Hardware, Software, Server, Security, Access, Database, Other
- priority: Low, Medium, High, Critical
- Choose the category that best matches the evidence in the transcript.
- If both Hardware and Network are possible, choose Hardware when the user is complaining about a physical device problem.
- Keep descriptions short and precise
- If info is missing, use "Unknown"
- Return only one valid JSON object.
- Do not include markdown, code fences, comments, explanation, or extra text before or after the JSON.
- Do not invent details that are not present in the transcript.
"""
        },
        {
            "role": "user",
            "content": f"Transcript: {text}"
        }
    ],
    "temperature": 0.0
}

print(f"\nUsing LLM model: {LLM_MODEL}")
print(f"Using LLM API: {LLM_API_URL}")

try:
    response = requests.post(LLM_API_URL, json=payload, timeout=60)
    response.raise_for_status()
    result = response.json()
except requests.exceptions.RequestException as exc:
    print("\nRemote model API request failed.")
    print(f"URL used: {LLM_API_URL}")
    if getattr(exc, "response", None) is not None:
        print(f"HTTP status: {exc.response.status_code}")
        print(f"Server response: {exc.response.text}")
    else:
        print("Check that the other device is on the same network, the model server is running,")
        print("the server is listening on LAN, and Windows Firewall allows the API port.")
    raise SystemExit(exc)
except ValueError as exc:
    print("\nThe remote API did not return valid JSON.")
    print(f"URL used: {LLM_API_URL}")
    raise SystemExit(exc)

print("\nLLM Response:\n")
llm_content = result["choices"][0]["message"]["content"].strip()

try:
    ticket = json.loads(llm_content)
except json.JSONDecodeError:
    ticket = {
        "category": "Other",
        "subcategory": "Unknown",
        "priority": "Medium",
        "issue": text if text else "Unknown",
        "affected_system": "Unknown",
        "location": "Unknown",
        "suggested_action": llm_content if llm_content else "Review the reported issue"
    }

print(json.dumps(ticket, indent=2))
