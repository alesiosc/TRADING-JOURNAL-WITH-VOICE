# Product Brief: Self-Contained STT Module

**Date:** 2026-04-01
**Author:** Cameron (via BMad Method)
**Status:** Draft

---

## 1. Problem Statement

The Trading Journal with Voice project currently relies exclusively on Zavi (zavivoice.com) for speech-to-text. Zavi is an external desktop application with its own reliability issues (agent mode hangs, clipboard bugs observed in testing 2026-03-27). There is no fallback, no offline option, and no way to run STT without Zavi installed.

The user has no strong GPU, so any local STT solution must be CPU-optimized.

## 2. Product Vision

A self-contained, portable Python STT module that:
- Provides an alternative to Zavi for speech-to-text
- Runs entirely offline on CPU using faster-whisper
- Uses toggle-style recording: one click to start, one click to stop, no time limits
- Outputs plain text that feeds directly into the existing Groq AI parser pipeline
- Is fully portable -- can be copied to another project with zero dependency on this codebase

## 3. Target User

Cameron -- solo trader who needs hands-free voice capture during live trading sessions. Cannot look away from charts to interact with software. Needs zero-friction recording that works reliably every time.

## 4. Core Requirements

### Must Have
- **Toggle recording**: Click once to start recording, click again to stop. No time limits.
- **CPU-only transcription**: Uses faster-whisper with CTranslate2 backend (int8 quantization)
- **Provider abstraction**: Clean interface so Zavi and faster-whisper are interchangeable
- **Config-driven selection**: YAML config file to choose between providers
- **Self-contained**: Single `stt_module/` directory, portable to other projects
- **Text output**: Returns plain text string, compatible with existing `SYSTEM_PROMPT` parser
- **Microphone selection**: Ability to pick which mic device to use

### Should Have
- **Hotkey support**: Keyboard shortcut to toggle recording (e.g., configurable key)
- **Visual indicator**: Simple console or status feedback showing recording state
- **Model selection**: Choose whisper model size (tiny/base/small) via config

### Won't Have (This Phase)
- Real-time streaming transcription (full clip transcribed after stop)
- Speaker diarization (who is speaking)
- GUI -- this is a backend module, UI integration comes later
- Direct Notion integration -- that stays in the existing pipeline

## 5. Success Criteria

1. Record a 30-second voice clip via toggle, get accurate text back in under 10 seconds on CPU
2. Swap between faster-whisper and Zavi (file-watcher mode) by changing one config value
3. Copy `stt_module/` to a fresh project, install deps, and it works standalone

## 6. Technical Constraints

- Python 3.13 (user's current version)
- Windows 10
- No NVIDIA GPU / no CUDA -- CPU only
- Must not conflict with existing project dependencies (groq, notion-client, watchdog, python-dotenv)

## 7. Relationship to Existing System

```
CURRENT FLOW:
  Zavi (Right Ctrl) → dictated text → text file / text area → Groq AI Parser → Notion

NEW FLOW (Option A - faster-whisper):
  stt_module (toggle record) → audio capture → faster-whisper → text → Groq AI Parser → Notion

NEW FLOW (Option B - Zavi, unchanged):
  Zavi (Right Ctrl) → dictated text → text area → Groq AI Parser → Notion
```

The STT module replaces ONLY the first step (voice → text). Everything downstream (AI parsing, Notion upload) remains unchanged.

## 8. Reference

- **faster-whisper**: https://github.com/SYSTRAN/faster-whisper -- CTranslate2 Whisper, 4x faster than openai/whisper on CPU
- **vivekuppal/transcribe**: https://github.com/vivekuppal/transcribe -- studied for audio capture patterns (pyaudio, wav processing, whisper integration). Code is too coupled to extract directly, but patterns are reusable.
- **Existing brainstorm**: `_bmad-output/planning-artifacts/brainstorming/brainstorming-session-2026-03-26-1805.md` -- Ideas #1 (Passive Listener), #5 (Voice-to-Structure Dictionary), #10 (Silent Confirm Mode) all relate to this module.
