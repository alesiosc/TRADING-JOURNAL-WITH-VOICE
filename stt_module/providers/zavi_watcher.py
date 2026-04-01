"""Zavi file-watcher provider implementation"""

import os
import time
from .base import STTProvider


class ZaviWatcherProvider(STTProvider):
    """
    Fallback provider that watches a text file for Zavi dictation output.
    User dictates with Zavi (Right Ctrl) into a designated text file.
    """
    
    def __init__(self):
        self.watch_file = None
    
    def initialize(self, config: dict):
        """Initialize the file watcher"""
        self.watch_file = config.get("output_file", "./zavi_output.txt")
        
        # Ensure file exists
        if not os.path.exists(self.watch_file):
            with open(self.watch_file, 'w', encoding='utf-8') as f:
                f.write("")
        
        print(f"✅ Zavi watcher initialized. Watching: {self.watch_file}")
    
    def transcribe(self, audio_file_path: str) -> str:
        """
        For Zavi, audio_file_path is ignored.
        Instead, read from the watched text file.
        """
        # Wait for file to be updated (simple polling)
        initial_mtime = os.path.getmtime(self.watch_file)
        
        print(f"⏳ Waiting for Zavi to write to {self.watch_file}...")
        timeout = 60  # 60 second timeout
        start_time = time.time()
        
        while True:
            time.sleep(0.5)
            current_mtime = os.path.getmtime(self.watch_file)
            
            if current_mtime > initial_mtime:
                break
            
            if time.time() - start_time > timeout:
                print("⚠️  Timeout waiting for Zavi input")
                return ""
        
        # Read the text
        with open(self.watch_file, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        
        # Clear the file for next use
        with open(self.watch_file, 'w', encoding='utf-8') as f:
            f.write("")
        
        return text
    
    def cleanup(self):
        """Cleanup resources"""
        pass
