# Architecture Document: Self-Contained STT Module

**Date:** 2026-04-01
**Author:** Cameron (via BMad Method)
**Status:** Draft

---

## 1. Overview

A self-contained Python module providing speech-to-text capabilities with a provider abstraction pattern. Supports both offline (faster-whisper) and external (Zavi file-watcher) providers, selectable via configuration.

---

## 2. Module Structure

```
stt_module/
├── __init__.py                 # Package exports
├── config.yaml                 # Configuration (provider, model, hotkey, mic)
├── providers/
│   ├── __init__.py
│   ├── base.py                 # Abstract STTProvider base class
│   ├── faster_whisper.py       # FasterWhisperProvider implementation
│   └── zavi_watcher.py         # ZaviWatcherProvider (file-based fallback)
├── audio_capture.py            # Microphone recording (pyaudio)
├── recorder.py                 # Toggle recording controller
├── hotkey_listener.py          # Keyboard hotkey support (pynput)
└── requirements.txt            # Module dependencies

# Integration point (in main project):
stt_integration.py              # Wrapper that calls stt_module and feeds to Groq parser
```

---

## 3. Provider Pattern

### Base Interface (`providers/base.py`)

```python
from abc import ABC, abstractmethod

class STTProvider(ABC):
    """Abstract base class for speech-to-text providers"""
    
    @abstractmethod
    def transcribe(self, audio_file_path: str) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_file_path: Path to WAV file
            
        Returns:
            Transcribed text string
        """
        pass
    
    @abstractmethod
    def initialize(self, config: dict) -> None:
        """Initialize provider with config"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources"""
        pass
```

### FasterWhisperProvider (`providers/faster_whisper.py`)

```python
from faster_whisper import WhisperModel
from .base import STTProvider

class FasterWhisperProvider(STTProvider):
    def __init__(self):
        self.model = None
        self.model_size = "base"
        self.device = "cpu"
        self.compute_type = "int8"  # CPU optimization
    
    def initialize(self, config: dict):
        self.model_size = config.get("model_size", "base")
        self.device = config.get("device", "cpu")
        self.compute_type = config.get("compute_type", "int8")
        
        # Load model (downloads on first run, cached after)
        self.model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type
        )
    
    def transcribe(self, audio_file_path: str) -> str:
        segments, info = self.model.transcribe(
            audio_file_path,
            beam_size=5,
            language="en"
        )
        
        # Combine all segments into single text
        text = " ".join([segment.text for segment in segments])
        return text.strip()
    
    def cleanup(self):
        # Model cleanup if needed
        self.model = None
```

### ZaviWatcherProvider (`providers/zavi_watcher.py`)

```python
from .base import STTProvider
import os
import time

class ZaviWatcherProvider(STTProvider):
    """
    Fallback provider that watches a text file for Zavi dictation output.
    User dictates with Zavi (Right Ctrl) into a designated text file.
    """
    
    def __init__(self):
        self.watch_file = None
    
    def initialize(self, config: dict):
        self.watch_file = config.get("zavi_output_file", "./zavi_output.txt")
        # Ensure file exists
        if not os.path.exists(self.watch_file):
            with open(self.watch_file, 'w') as f:
                f.write("")
    
    def transcribe(self, audio_file_path: str) -> str:
        """
        For Zavi, audio_file_path is ignored.
        Instead, read from the watched text file.
        """
        # Wait for file to be updated (simple polling)
        initial_mtime = os.path.getmtime(self.watch_file)
        
        print(f"Waiting for Zavi to write to {self.watch_file}...")
        while True:
            time.sleep(0.5)
            current_mtime = os.path.getmtime(self.watch_file)
            if current_mtime > initial_mtime:
                break
        
        # Read the text
        with open(self.watch_file, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        
        # Clear the file for next use
        with open(self.watch_file, 'w') as f:
            f.write("")
        
        return text
    
    def cleanup(self):
        pass
```

---

## 4. Audio Capture (`audio_capture.py`)

```python
import pyaudio
import wave
import tempfile
import os

class AudioCapture:
    def __init__(self, device_index=None, sample_rate=16000, channels=1):
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = 1024
        self.format = pyaudio.paInt16
        
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
    
    def start_recording(self):
        """Start capturing audio from microphone"""
        self.frames = []
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.chunk
        )
        print("🎤 Recording started...")
    
    def stop_recording(self) -> str:
        """Stop recording and save to temp WAV file"""
        print("⏹️  Recording stopped.")
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        # Save to temp file
        fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))
        
        return temp_path
    
    def record_chunk(self):
        """Record one chunk (called in loop while recording)"""
        if self.stream:
            data = self.stream.read(self.chunk, exception_on_overflow=False)
            self.frames.append(data)
    
    def cleanup(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
    
    @staticmethod
    def list_devices():
        """List available microphone devices"""
        audio = pyaudio.PyAudio()
        print("\nAvailable microphone devices:")
        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  [{i}] {info['name']}")
        audio.terminate()
```

---

## 5. Toggle Recorder (`recorder.py`)

```python
import threading
import time
from .audio_capture import AudioCapture
from .providers.base import STTProvider

class ToggleRecorder:
    def __init__(self, provider: STTProvider, audio_capture: AudioCapture):
        self.provider = provider
        self.audio_capture = audio_capture
        self.is_recording = False
        self.recording_thread = None
    
    def toggle(self):
        """Toggle recording on/off"""
        if self.is_recording:
            self.stop()
        else:
            self.start()
    
    def start(self):
        """Start recording"""
        if self.is_recording:
            return
        
        self.is_recording = True
        self.audio_capture.start_recording()
        
        # Start recording loop in background thread
        self.recording_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.recording_thread.start()
    
    def stop(self) -> str:
        """Stop recording and return transcribed text"""
        if not self.is_recording:
            return ""
        
        self.is_recording = False
        
        # Wait for recording thread to finish
        if self.recording_thread:
            self.recording_thread.join()
        
        # Save audio to file
        audio_file = self.audio_capture.stop_recording()
        
        # Transcribe
        print("🔄 Transcribing...")
        text = self.provider.transcribe(audio_file)
        print(f"✅ Transcription: {text}")
        
        # Cleanup temp file
        import os
        os.unlink(audio_file)
        
        return text
    
    def _record_loop(self):
        """Background loop to capture audio chunks"""
        while self.is_recording:
            self.audio_capture.record_chunk()
            time.sleep(0.01)  # Small delay to prevent CPU spinning
```

---

## 6. Hotkey Listener (`hotkey_listener.py`)

```python
from pynput import keyboard

class HotkeyListener:
    def __init__(self, hotkey: str, callback):
        """
        Args:
            hotkey: String like "ctrl+shift+r" or "f9"
            callback: Function to call when hotkey pressed
        """
        self.hotkey = hotkey
        self.callback = callback
        self.listener = None
    
    def start(self):
        """Start listening for hotkey"""
        # Parse hotkey string
        hotkey_combo = keyboard.HotKey(
            keyboard.HotKey.parse(self.hotkey),
            self.callback
        )
        
        def for_canonical(f):
            return lambda k: f(self.listener.canonical(k))
        
        self.listener = keyboard.Listener(
            on_press=for_canonical(hotkey_combo.press),
            on_release=for_canonical(hotkey_combo.release)
        )
        self.listener.start()
        print(f"⌨️  Hotkey listener started: {self.hotkey}")
    
    def stop(self):
        """Stop listening"""
        if self.listener:
            self.listener.stop()
```

---

## 7. Configuration (`config.yaml`)

```yaml
# STT Module Configuration

# Provider selection: "faster_whisper" or "zavi_watcher"
provider: faster_whisper

# FasterWhisper settings (only used if provider = faster_whisper)
faster_whisper:
  model_size: base          # Options: tiny, base, small, medium, large
  device: cpu               # Options: cpu, cuda
  compute_type: int8        # Options: int8, int16, float16, float32
  language: en              # Language code

# Zavi Watcher settings (only used if provider = zavi_watcher)
zavi_watcher:
  output_file: ./zavi_output.txt

# Audio capture settings
audio:
  device_index: null        # null = default mic, or specify device number
  sample_rate: 16000        # 16kHz is standard for Whisper
  channels: 1               # Mono

# Hotkey settings
hotkey:
  enabled: true
  key: <ctrl>+<shift>+r     # Hotkey to toggle recording
```

---

## 8. Main Module Interface (`__init__.py`)

```python
import yaml
from .providers.faster_whisper import FasterWhisperProvider
from .providers.zavi_watcher import ZaviWatcherProvider
from .audio_capture import AudioCapture
from .recorder import ToggleRecorder
from .hotkey_listener import HotkeyListener

class STTModule:
    def __init__(self, config_path="config.yaml"):
        # Load config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize provider
        provider_name = self.config['provider']
        if provider_name == "faster_whisper":
            self.provider = FasterWhisperProvider()
            self.provider.initialize(self.config['faster_whisper'])
        elif provider_name == "zavi_watcher":
            self.provider = ZaviWatcherProvider()
            self.provider.initialize(self.config['zavi_watcher'])
        else:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        # Initialize audio capture
        audio_config = self.config['audio']
        self.audio_capture = AudioCapture(
            device_index=audio_config.get('device_index'),
            sample_rate=audio_config.get('sample_rate', 16000),
            channels=audio_config.get('channels', 1)
        )
        
        # Initialize recorder
        self.recorder = ToggleRecorder(self.provider, self.audio_capture)
        
        # Initialize hotkey listener (optional)
        self.hotkey_listener = None
        if self.config['hotkey']['enabled']:
            self.hotkey_listener = HotkeyListener(
                self.config['hotkey']['key'],
                self.recorder.toggle
            )
    
    def start(self):
        """Start the STT module (hotkey listener if enabled)"""
        if self.hotkey_listener:
            self.hotkey_listener.start()
    
    def toggle_recording(self):
        """Manually toggle recording (if not using hotkey)"""
        self.recorder.toggle()
    
    def get_last_transcription(self) -> str:
        """Get the last transcribed text"""
        return self.recorder.stop()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.audio_capture.cleanup()
        self.provider.cleanup()

# Convenience function
def create_stt_module(config_path="config.yaml") -> STTModule:
    return STTModule(config_path)
```

---

## 9. Dependencies (`requirements.txt`)

```
# Core STT
faster-whisper>=1.0.0       # CPU-optimized Whisper

# Audio capture
pyaudio>=0.2.14             # Microphone recording
wave                        # WAV file handling (built-in)

# Hotkey support
pynput>=1.7.6               # Keyboard listener

# Config
pyyaml>=6.0                 # YAML config parsing

# Utilities
python-dotenv>=1.0.0        # Optional: if API keys needed later
```

---

## 10. Integration with Existing Project

### Option A: Direct Integration in `trading_journal_final.py`

Add a button "Record with STT Module" that:
1. Calls `stt_module.toggle_recording()`
2. On second click, gets text via `stt_module.get_last_transcription()`
3. Inserts text into the existing text area
4. Existing "Save Trade" button sends to Groq parser as usual

### Option B: Standalone Script (`stt_integration.py`)

```python
from stt_module import create_stt_module
from groq import Groq
from notion_client import Client
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize STT module
stt = create_stt_module("stt_module/config.yaml")
stt.start()

# Initialize Groq and Notion (existing pipeline)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
notion = Client(auth=os.getenv("NOTION_TOKEN"))

print("STT Module ready. Press Ctrl+Shift+R to toggle recording.")
print("Press Ctrl+C to exit.")

try:
    while True:
        # Hotkey listener runs in background
        # When recording stops, get text and process
        import time
        time.sleep(1)
except KeyboardInterrupt:
    stt.cleanup()
    print("Exiting.")
```

---

## 11. Performance Expectations (CPU-only)

| Model | Size | Speed (CPU) | Accuracy |
|-------|------|-------------|----------|
| tiny  | 39 MB | ~2x real-time | Good for short clips |
| base  | 74 MB | ~1x real-time | Recommended for trading journal |
| small | 244 MB | ~0.5x real-time | Better accuracy, slower |

**Recommendation:** Start with `base` model. 30-second clip transcribes in ~30 seconds on modern CPU.

---

## 12. Portability Checklist

To use this module in another project:
1. Copy `stt_module/` directory
2. Install dependencies: `pip install -r stt_module/requirements.txt`
3. Edit `stt_module/config.yaml` to set provider and hotkey
4. Import: `from stt_module import create_stt_module`
5. Use: `stt = create_stt_module(); stt.start()`

No dependencies on Notion, Groq, or any project-specific code.

---

## 13. Testing Plan

1. **Unit test providers**: Mock audio file, verify transcription output
2. **Test audio capture**: Record 5-second clip, verify WAV file created
3. **Test toggle recorder**: Start/stop multiple times, verify no memory leaks
4. **Test hotkey**: Verify Ctrl+Shift+R triggers toggle
5. **Integration test**: Record voice → transcribe → feed to Groq parser → verify Notion entry

---

## 14. Future Enhancements (Out of Scope)

- Real-time streaming transcription (partial results while speaking)
- Voice activity detection (auto-stop when silence detected)
- Multiple language support
- Cloud provider support (Deepgram, AssemblyAI)
- GUI with waveform visualization

---

**End of Architecture Document**
