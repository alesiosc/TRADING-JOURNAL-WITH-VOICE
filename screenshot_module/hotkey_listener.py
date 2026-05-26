"""Global hotkey listener using pynput.

User-configurable key combo — defined in config.yaml under hotkey.key.
Supports pynput's HotKey.parse() format:
  <ctrl>+<shift>+s
  <ctrl>+<alt>+<print_screen>
  <scroll_lock>
  <f9>
  etc.
"""

from pynput import keyboard
import threading


class HotkeyListener:
    """Listens for a global hotkey combination and triggers a callback."""

    def __init__(self, hotkey: str, callback):
        """
        Args:
            hotkey: String in pynput format e.g. "<ctrl>+<shift>+s"
            callback: Zero-argument callable invoked when the hotkey is pressed.
        """
        self.hotkey_str = hotkey
        self.callback = callback
        self._listener = None
        self._thread = None

    def start(self):
        """Start listening for the hotkey combination on a background thread."""
        if self._listener is not None:
            return  # already started

        hotkey_combo = keyboard.HotKey(
            keyboard.HotKey.parse(self.hotkey_str),
            self._on_activate,
        )

        def for_canonical(f):
            return lambda k: f(self._listener.canonical(k))

        def run_listener():
            with keyboard.Listener(
                on_press=for_canonical(hotkey_combo.press),
                on_release=for_canonical(hotkey_combo.release),
            ) as listener:
                self._listener = listener
                listener.join()

        self._thread = threading.Thread(target=run_listener, daemon=True, name="hotkey-listener")
        self._thread.start()

    def _on_activate(self):
        """Called when the hotkey combination is pressed."""
        try:
            self.callback()
        except Exception as e:
            print(f"⚠️  Hotkey callback error: {e}")

    def stop(self):
        """Stop the hotkey listener."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        self._thread = None
