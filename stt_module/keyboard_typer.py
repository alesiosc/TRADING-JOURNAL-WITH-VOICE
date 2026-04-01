"""Keyboard typer - simulates typing into focused window"""

from pynput.keyboard import Controller, Key
import time


class KeyboardTyper:
    """Types text into the currently focused window"""
    
    def __init__(self, typing_speed=0.01):
        """
        Args:
            typing_speed: Delay between keystrokes in seconds (default 0.01 = fast)
        """
        self.keyboard = Controller()
        self.typing_speed = typing_speed
    
    def type_text(self, text: str):
        """
        Type the given text into the currently focused window.
        
        Args:
            text: Text to type
        """
        if not text:
            return
        
        print(f"⌨️  Typing text into focused window...")
        
        # Small delay to ensure window is ready
        time.sleep(0.1)
        
        # Type each character
        for char in text:
            self.keyboard.type(char)
            time.sleep(self.typing_speed)
        
        print("✅ Typing complete")
    
    def type_with_newline(self, text: str):
        """Type text and press Enter at the end"""
        self.type_text(text)
        self.keyboard.press(Key.enter)
        self.keyboard.release(Key.enter)
