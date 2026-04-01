import sys
import os
import tkinter as tk
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class STTController:
    def __init__(self):
        self.stt = None
        self.recording = False
        self.ready = False
        self.buttons = []
        self.windows = []
        self.root = None
        self.target_window = None
        
    def init_stt(self):
        print("Loading STT module...")
        from stt_module import create_stt_module
        self.stt = create_stt_module("config.yaml")
        self.stt.start()
        self.ready = True
        print("Ready! Click any button to record.")
        
    def toggle(self, clicked_from_window):
        if not self.ready:
            print("Still loading, please wait...")
            return
        
        print(f"Toggle: recording={self.recording}")
        
        # If starting recording, use the window that was passed in (captured before click)
        if not self.recording:
            self.target_window = clicked_from_window
            print(f"Will type into window: {self.target_window}")
        
        self.recording = not self.recording
        
        # Update button colors
        for btn in self.buttons:
            if self.recording:
                btn.config(bg="#e74c3c", text="■")
            else:
                btn.config(bg="#2ecc71", text="●")
        
        # Do the actual recording toggle in background
        def do_toggle():
            # Restore focus BEFORE transcription so typing goes to right window
            # self.recording is already flipped, so False = we just stopped
            if not self.recording and self.target_window:
                try:
                    import win32gui
                    time.sleep(0.2)
                    win32gui.SetForegroundWindow(self.target_window)
                    print(f"Restored focus to: {self.target_window}")
                    time.sleep(0.3)
                except Exception as e:
                    print(f"Focus error: {e}")
            self.stt.toggle_recording()
        
        threading.Thread(target=do_toggle, daemon=True).start()
        
    def exit_all(self):
        print("Exiting...")
        if self.stt:
            self.stt.cleanup()
        for window in self.windows:
            try:
                window.destroy()
            except:
                pass
        if self.root:
            self.root.quit()

def create_floating_button(parent, x, y, label, controller):
    window = tk.Toplevel(parent)
    window.title(f"STT {label}")
    window.overrideredirect(True)
    window.attributes("-topmost", True)
    window.wm_attributes("-alpha", 0.95)
    window.geometry(f"28x28+{x}+{y}")
    window.configure(bg="black")

    # Main button area
    btn = tk.Label(
        window,
        text="●",
        font=("Arial", 12, "bold"),
        bg="#2ecc71",
        fg="white",
        cursor="hand2",
        relief="flat",
        bd=0
    )
    btn.pack(fill="both", expand=True)

    # State
    btn._captured_window = None
    btn._handle_visible = False

    # Drag handle - hidden by default, shown on hover
    handle = tk.Frame(window, bg="#888888", height=6, cursor="fleur")

    def show_handle(e):
        if not btn._handle_visible:
            handle.place(x=0, y=0, relwidth=1.0, height=6)
            btn._handle_visible = True
        # Capture focused window on hover
        try:
            import win32gui
            fg = win32gui.GetForegroundWindow()
            btn._captured_window = fg
        except:
            pass

    def hide_handle(e):
        # Check if mouse truly left the window
        wx = window.winfo_rootx()
        wy = window.winfo_rooty()
        ww = window.winfo_width()
        wh = window.winfo_height()
        mx = e.x_root
        my = e.y_root
        if mx < wx or mx > wx + ww or my < wy or my > wy + wh:
            handle.place_forget()
            btn._handle_visible = False

    # Button click = toggle recording (only on btn, not handle)
    def on_btn_click(e):
        target = btn._captured_window
        print(f"[M{label}] Toggle with: {target}")
        controller.toggle(target)

    # Handle drag = move window
    handle._dx = 0
    handle._dy = 0

    def on_handle_press(e):
        handle._dx = e.x
        handle._dy = e.y

    def on_handle_drag(e):
        nx = window.winfo_x() + e.x - handle._dx
        ny = window.winfo_y() + e.y - handle._dy
        window.geometry(f"+{nx}+{ny}")

    # Bindings
    window.bind("<Enter>", show_handle)
    window.bind("<Leave>", hide_handle)
    btn.bind("<Button-1>", on_btn_click)
    handle.bind("<ButtonPress-1>", on_handle_press)
    handle.bind("<B1-Motion>", on_handle_drag)

    # Right-click menu
    menu = tk.Menu(window, tearoff=0)
    menu.add_command(label="Exit All", command=controller.exit_all)
    window.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))
    btn.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))
    handle.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    controller.buttons.append(btn)
    return window

def main():
    print("="*60)
    print("STT GUI - Starting...")
    print("="*60)
    
    root = tk.Tk()
    root.withdraw()
    
    controller = STTController()
    controller.root = root
    
    # Try to detect monitors
    try:
        from screeninfo import get_monitors
        monitors = get_monitors()
        positions = []
        for i, m in enumerate(monitors[:4], 1):
            x = m.x + 50
            y = m.y + 50
            positions.append((x, y, f"M{i}"))
        print(f"Detected {len(monitors)} monitors")
        for i, (x, y, label) in enumerate(positions):
            print(f"  Monitor {i+1}: Button at ({x}, {y})")
    except Exception as e:
        print(f"Could not detect monitors: {e}")
        print("Install screeninfo: pip install screeninfo")
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        positions = [
            (50, 50, "1"),
            (screen_w - 150, 50, "2"),
            (50, screen_h - 150, "3"),
            (screen_w - 150, screen_h - 150, "4")
        ]
        print(f"Using single screen fallback: {screen_w}x{screen_h}")
    
    print("\nCreating buttons...")
    for x, y, label in positions:
        window = create_floating_button(root, x, y, label, controller)
        controller.windows.append(window)
    
    print("\nButtons created!")
    print("USAGE:")
    print("1. Click into your target window (Notepad, browser, etc.)")
    print("2. Click any MIC button to start recording")
    print("3. Speak your message")
    print("4. Click STOP button")
    print("5. Text will type into your target window")
    print("Right-click any button to exit")
    print("="*60)
    
    threading.Thread(target=controller.init_stt, daemon=True).start()
    
    root.mainloop()

if __name__ == "__main__":
    main()
