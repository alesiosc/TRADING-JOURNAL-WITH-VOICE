"""Main STT Module interface"""

import yaml
import os
from .providers.faster_whisper import FasterWhisperProvider
from .providers.zavi_watcher import ZaviWatcherProvider
from .audio_capture import AudioCapture
from .recorder import ToggleRecorder
from .hotkey_listener import HotkeyListener
from .keyboard_typer import KeyboardTyper


class STTModule:
    """Main interface for the STT module"""
    
    def __init__(self, config_path="config.yaml"):
        # Load config
        # If config_path is relative, make it relative to the module directory
        if not os.path.isabs(config_path):
            # Check if it's already a full path to the config file
            if os.path.exists(config_path):
                config_full_path = config_path
            else:
                # Otherwise, assume it's just the filename and look in module directory
                config_full_path = os.path.join(os.path.dirname(__file__), os.path.basename(config_path))
        else:
            config_full_path = config_path
            
        with open(config_full_path, 'r') as f:
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
        
        # Initialize keyboard typer (optional)
        self.typer = None
        auto_type = self.config.get('auto_type', {}).get('enabled', False)
        if auto_type:
            typing_speed = self.config.get('auto_type', {}).get('typing_speed', 0.01)
            self.typer = KeyboardTyper(typing_speed=typing_speed)
        
        # Initialize recorder
        self.recorder = ToggleRecorder(self.provider, self.audio_capture, auto_type=auto_type, typer=self.typer)
        
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
        print("✅ STT Module started")
    
    def toggle_recording(self):
        """Manually toggle recording (if not using hotkey)"""
        self.recorder.toggle()
    
    def get_last_transcription(self) -> str:
        """Get the last transcribed text"""
        return self.recorder.get_last_transcription()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.audio_capture.cleanup()
        self.provider.cleanup()
        print("✅ STT Module cleaned up")


def create_stt_module(config_path="config.yaml") -> STTModule:
    """Convenience function to create STT module"""
    return STTModule(config_path)
