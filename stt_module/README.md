# STT Module - Self-Contained Speech-to-Text

A portable Python module for speech-to-text with toggle recording.

## Installation

```bash
pip install -r stt_module/requirements.txt
```

## Quick Start

```python
from stt_module import create_stt_module

# Create and start module
stt = create_stt_module("stt_module/config.yaml")
stt.start()

# Press Ctrl+Shift+R to toggle recording
# Transcribed text will be printed to console
```

## Configuration

Edit `stt_module/config.yaml`:

- **provider**: Choose `faster_whisper` (offline) or `zavi_watcher` (file-based)
- **model_size**: tiny, base, small, medium, large
- **hotkey**: Customize the toggle key

## Testing

Run the test script:

```bash
python test_stt.py
```

Press Ctrl+Shift+R to start recording, speak, then press Ctrl+Shift+R again to stop and transcribe.

## Architecture

See `_bmad-output/planning-artifacts/stt-module-architecture.md` for full technical details.
