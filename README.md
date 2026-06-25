# AI-Powered Speech-to-Ticket Automation for BHEL DIGIT Service Requests

This project records a user's voice complaint, transcribes it with Faster Whisper, and sends the transcript to an OpenAI-compatible local LLM API to generate a structured IT support ticket.

## Current Scope

- Voice recording from microphone input
- Speech-to-text transcription using Faster Whisper
- IT support ticket extraction using a local/remote LLM endpoint
- JSON output with category, priority, issue, affected system, location, and suggested action
- Intended integration with the BHEL DIGIT Service Request page

## Setup

```powershell
python -m venv vir
.\vir\Scripts\activate
pip install -r requirements.txt
```

## Run

```powershell
python voice_to_llm.py
```

Optional environment variables:

```powershell
$env:LLM_API_URL="http://<host>:<port>/v1/chat/completions"
$env:WHISPER_MODEL="medium"
```
