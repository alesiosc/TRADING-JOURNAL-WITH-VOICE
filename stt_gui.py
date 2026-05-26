"""STT GUI - Floating mic buttons with window tracking and drag handle

Each monitor gets a tiny floating dot. Click to toggle recording.
Drag via the gray handle bar. Background thread polls for the real focused window.
"""
import sys
import os
import tkinter as tk
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class WindowTracker:
    """Periodically polls foreground window, ignoring our own overlay windows."""

    def __init__(self):
        self._target = None
        self._our_windows = []
        self._running = True
        self._lock = threading.Lock()
        self._thread = None

    def add_window(self, hwnd):
        self._our_windows.append(hwnd)

    def start(self):
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def get_target(self):
        with self._lock:
            return self._target

    def _poll(self):
        import win32gui
        while self._running:
            try:
                fg = win32gui.GetForegroundWindow()
                if fg and fg not in self._our_windows:
                    with self._lock:
                        self._target = fg
            except Exception:
                pass
            time.sleep(0.3)


class STTController:
    def __init__(self):
        self.stt = None
        self.recording = False
        self.ready = False
        self.buttons = []
        self.windows = []
        self.root = None
        self.window_tracker = WindowTracker()

    def init_stt(self):
        print("Loading STT module...")
        from stt_module import create_stt_module
        self.stt = create_stt_module("stt_module/config.yaml")
        self.stt.start()
        self.ready = True
        self.window_tracker.start()
        print("Ready! Hover button to capture window, click to record.")

    def toggle(self):
        if not self.ready:
            print("Still loading, please wait...")
            return

        target = self.window_tracker.get_target()
        print(f"Toggle: recording={self.recording}, target_window={target}")

        self.recording = not self.recording

        # Update button colors
        for btn in self.buttons:
            if self.recording:
                btn.config(bg="#e74c3c", text="\u25a0")
            else:
                btn.config(bg="#2ecc71", text="\u25cf")

        # Do actual work in background
        def do_toggle():
            if not self.recording and target:
                try:
                    import win32gui
                    time.sleep(0.15)
                    win32gui.SetForegroundWindow(target)
                    print(f"Restored focus to: {target}")
                    time.sleep(0.2)
                except Exception as e:
                    print(f"Focus restore error: {e}")
            self.stt.toggle_recording()

        threading.Thread(target=do_toggle, daemon=True).start()

    def exit_all(self):
        print("Exiting...")
        self.window_tracker.stop()
        if self.stt:
            try:
                self.stt.cleanup()
            except Exception:
                pass
        for window in self.windows:
            try:
                window.destroy()
            except Exception:
                pass
        if self.root:
            self.root.quit()
        os._exit(0)


def create_floating_button(parent, x, y, label, controller):
    window = tk.Toplevel(parent)
    window.title(f"STT {label}")
    window.overrideredirect(True)
    window.attributes("-topmost", True)
    window.wm_attributes("-alpha", 0.95)
    window.configure(bg="black")

    # Register window handle for tracker to ignore
    try:
        hwnd = frame_hwnd(window)
        controller.window_tracker.add_window(hwnd)
    except Exception:
        pass

    # Outer frame: 10x10 mic area + 4px handle on top = 10x14
    total_w = 10
    handle_h = 4
    btn_h = 10
    window.geometry(f"{total_w}x{handle_h + btn_h}+{x}+{y}")

    # === Drag handle (4px tall, full width, gray) ===
    handle = tk.Frame(window, bg="#888888", cursor="fleur", height=handle_h)
    handle.pack(fill="x", side="top")

    # === Mic button (10x10, green dot) ===
    btn = tk.Label(
        window,
        text="\u25cf",
        font=("Arial", 5, "bold"),
        bg="#2ecc71",
        fg="white",
        cursor="hand2",
        relief="flat",
        bd=0,
    )
    btn.pack(fill="both", expand=True)

    # Drag handle state
    handle._dx = 0
    handle._dy = 0

    def on_handle_press(e):
        handle._dx = e.x
        handle._dy = e.y

    def on_handle_drag(e):
        nx = window.winfo_x() + e.x - handle._dx
        ny = window.winfo_y() + e.y - handle._dy
        window.geometry(f"+{nx}+{ny}")

    # Button click = toggle recording
    def on_btn_click(e):
        print(f"[M{label}] Button clicked")
        controller.toggle()

    # Right-click menu
    menu = tk.Menu(window, tearoff=0)
    menu.add_command(label="Exit All", command=controller.exit_all)

    # Bind events
    handle.bind("<ButtonPress-1>", on_handle_press)
    handle.bind("<B1-Motion>", on_handle_drag)
    btn.bind("<Button-1>", on_btn_click)

    window.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))
    btn.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))
    handle.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    controller.buttons.append(btn)
    return window


def frame_hwnd(window):
    """Get the Windows HWND for a tkinter window."""
    import ctypes
    if sys.platform == "win32":
        return ctypes.windll.user32.GetParent(window.winfo_id())
    return None


def main():
    print("=" * 60)
    print("STT GUI - Starting...")
    print("=" * 60)

    root = tk.Tk()
    root.withdraw()

    controller = STTController()
    controller.root = root

    # Detect monitors
    try:
        from screeninfo import get_monitors
        monitors = get_monitors()
        positions = []
        for i, m in enumerate(monitors[:4], 1):
            x = m.x + 30
            y = m.y + 30
            positions.append((x, y, f"M{i}"))
        print(f"Detected {len(monitors)} monitors")
    except Exception as e:
        print(f"Could not detect monitors: {e}")
        print("Install screeninfo: pip install screeninfo")
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        positions = [
            (30, 30, "1"),
            (screen_w - 80, 30, "2"),
            (30, screen_h - 80, "3"),
            (screen_w - 80, screen_h - 80, "4"),
        ]

    print("\nCreating buttons...")
    for px, py, label in positions:
        window = create_floating_button(root, px, py, label, controller)
        controller.windows.append(window)

    print("\nButtons created!")
    print("USAGE:")
    print("  - Drag gray handle bar = move button")
    print("  - Click green dot = toggle recording (start/stop)")
    print("  - Right-click anywhere = exit menu")
    print("  - Window tracked automatically (polls every 300ms)")
    print("=" * 60)

    threading.Thread(target=controller.init_stt, daemon=True).start()
    root.mainloop()


if __name__ == "__main__":
    main()
