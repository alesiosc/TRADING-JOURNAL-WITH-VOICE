"""Toggle recorder with threading"""

import threading
import time
import os
from .audio_capture import AudioCapture
from .providers.base import STTProvider


class ToggleRecorder:
    """Manages toggle recording with background thread"""
    
    def __init__(self, provider: STTProvider, audio_capture: AudioCapture, auto_type=False, typer=None):
        self.provider = provider
        self.audio_capture = audio_capture
        self.is_recording = False
        self.recording_thread = None
        self.last_transcription = ""
        self.auto_type = auto_type
        self.typer = typer
    
    def toggle(self):
        """Toggle recording on/off"""
        if self.is_recording:
            self.stop()
        else:
            self.start()
    
    def start(self):
        """Start recording"""
        if self.is_recording:
            print("⚠️  Already recording")
            return
        
        self.is_recording = True
        self.audio_capture.start_recording()
        
        # Start recording loop in background thread
        self.recording_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.recording_thread.start()
    
    def stop(self) -> str:
        """Stop recording and return transcribed text"""
        if not self.is_recording:
            print("⚠️  Not currently recording")
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
        self.last_transcription = text
        print(f"✅ Transcription: {text}")
        
        # Cleanup temp file
        os.unlink(audio_file)
        
        # Auto-type if enabled
        if self.auto_type and self.typer and text:
            self.typer.type_text(text)
        
        return text
    
    def get_last_transcription(self) -> str:
        """Get the last transcribed text"""
        return self.last_transcription
    
    def _record_loop(self):
        """Background loop to capture audio chunks"""
        while self.is_recording:
            self.audio_capture.record_chunk()
            time.sleep(0.01)  # Small delay to prevent CPU spinning
