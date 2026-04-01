"""Hotkey listener using pynput"""

from pynput import keyboard


class HotkeyListener:
    """Listens for keyboard hotkey and triggers callback"""
    
    def __init__(self, hotkey: str, callback):
        """
        Args:
            hotkey: String like "<ctrl>+<shift>+r" or "<f9>"
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
