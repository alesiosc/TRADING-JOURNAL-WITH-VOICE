path = r'D:\MyPythonProjects_2\TRADING JOURNAL WITH VOICE\stt_gui.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Fix 2: Replace create_floating_button - half size + hover drag handle
old_func = '''def create_floating_button(parent, x, y, label, controller):
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
    return window'''

new_func = '''def create_floating_button(parent, x, y, label, controller):
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
    return window'''

if old_func in c:
    c = c.replace(old_func, new_func)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print("FIXED: buttons 28x28, hover drag handle, separate click/drag")
else:
    print("ERROR: old function not found")
    # Debug: show what's around line 68
    lines = c.split('\n')
    for i in range(67, min(80, len(lines))):
        print(f"{i+1}: {repr(lines[i])}")