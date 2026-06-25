# Fully Local AI Voice-to-Ticket System for BHEL DIGIT Service Requests

This project records an employee's voice complaint, transcribes it locally with Faster Whisper, sends the transcript over LAN to an LM Studio server running a local LLM on another device, and returns a structured IT support ticket in JSON format.

The goal is to support future integration with the BHEL DIGIT Service Request page while keeping the AI pipeline local to the machine/LAN instead of relying on cloud AI APIs.

## Architecture

```text
Microphone input
    -> local audio recording
    -> local Faster Whisper transcription
    -> LAN request to LM Studio OpenAI-compatible API
    -> local LLM ticket extraction
    -> structured JSON ticket output
```

## Current Scope

- Records microphone audio locally
- Saves the recording as `audio.wav`
- Transcribes speech using Faster Whisper on CPU
- Uses prompt guidance for English, Telugu, Hindi, and mixed IT terminology
- Connects to a LAN-hosted LM Studio LLM endpoint
- Produces ticket-ready JSON with category, priority, issue, affected system, location, and suggested action
- Intended for later DIGIT Service Request integration

## Ticket Output Format

```json
{
  "category": "Hardware",
  "subcategory": "Printer",
  "priority": "Medium",
  "issue": "Printer is not working",
  "affected_system": "Printer",
  "location": "Unknown",
  "suggested_action": "Check printer power, cable, driver, and queue status"
}
```

## Setup

```powershell
python -m venv vir
.\vir\Scripts\activate
pip install -r requirements.txt
```

Copy the example environment file and update it for your local LM Studio host:

```powershell
copy .env.example .env
```

Example values:

```powershell
$env:LLM_API_URL="http://<lm-studio-host-ip>:1234/v1/chat/completions"
$env:LLM_MODEL="qwen3.5-9b-sft-claude-opus-reasoning-unsloth"
$env:WHISPER_MODEL="medium"
```

## Run

Start the LM Studio server on the other/local device first, then run:

```powershell
python voice_to_llm.py
```

## Resume Summary

Built a fully local AI voice-to-ticket pipeline using Faster Whisper for offline speech transcription and a LAN-connected LM Studio LLM server for structured JSON ticket generation, enabling private IT support automation without cloud AI API dependency.
