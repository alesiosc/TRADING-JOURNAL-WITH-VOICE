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
                btn.config(bg="#e74c3c", text="STOP")
            else:
                btn.config(bg="#2ecc71", text="MIC")
        
        # Do the actual recording toggle in background
        def do_toggle():
            self.stt.toggle_recording()
            # After transcription completes, restore focus to target window
            if not self.recording and self.target_window:
                try:
                    import win32gui
                    time.sleep(0.5)
                    win32gui.SetForegroundWindow(self.target_window)
                    print(f"Restored focus to window: {self.target_window}")
                except Exception as e:
                    print(f"Could not restore window focus: {e}")
        
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
    window.geometry(f"56x56+{x}+{y}")
    window.configure(bg="black")
    
    btn = tk.Label(
        window, 
        text="MIC", 
        font=("Arial", 9, "bold"), 
        bg="#2ecc71", 
        fg="white", 
        cursor="hand2", 
        relief="raised", 
        bd=2
    )
    btn.pack(fill="both", expand=True, padx=2, pady=2)
    
    # Capture the foreground window BEFORE the button gets focus
    def on_click(e):
        # Only toggle if not dragging
        if abs(e.x - btn._click_x) < 5 and abs(e.y - btn._click_y) < 5:
            try:
                import win32gui
                # Get the window that had focus before this button was clicked
                target = btn._captured_window
                controller.toggle(target)
            except:
                controller.toggle(None)
    
    def on_press(e):
        # Capture the foreground window at the moment of press
        try:
            import win32gui
            btn._captured_window = win32gui.GetForegroundWindow()
        except:
            btn._captured_window = None
        
        btn._click_x = e.x
        btn._click_y = e.y
        btn._drag_x = e.x
        btn._drag_y = e.y
    
    def on_drag(e):
        x = window.winfo_x() + e.x - btn._drag_x
        y = window.winfo_y() + e.y - btn._drag_y
        window.geometry(f"+{x}+{y}")
    
    btn._click_x = 0
    btn._click_y = 0
    btn._drag_x = 0
    btn._drag_y = 0
    btn._captured_window = None
    
    btn.bind("<ButtonPress-1>", on_press)
    btn.bind("<B1-Motion>", on_drag)
    btn.bind("<ButtonRelease-1>", on_click)
    
    # Right-click menu
    menu = tk.Menu(window, tearoff=0)
    menu.add_command(label="Exit All", command=controller.exit_all)
    window.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))
    btn.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))
    
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
