# Update checklist styling - bigger headers, subtext underneath

with open('trading_journal_final.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the checklist rendering code
old_rendering = '''for item, hint in checklist_data:
            frame = tk.Frame(left_panel, bg="#f5f5f5")
            frame.pack(fill="x", padx=10, pady=2)
            
            var = tk.BooleanVar()
            self.checklist_items[item] = var
            
            cb = tk.Checkbutton(frame, variable=var, bg="#f5f5f5")
            cb.pack(side="left")
            
            tk.Label(frame, text=f"{item}", font=("Arial", 9, "bold"), bg="#f5f5f5", anchor="w").pack(side="left")
            tk.Label(frame, text=f" ({hint})", font=("Arial", 8), fg="#666", bg="#f5f5f5", anchor="w").pack(side="left")'''

new_rendering = '''for item, hint in checklist_data:
            frame = tk.Frame(left_panel, bg="#f5f5f5")
            frame.pack(fill="x", padx=10, pady=4)
            
            var = tk.BooleanVar()
            self.checklist_items[item] = var
            
            # Checkbox on left
            cb = tk.Checkbutton(frame, variable=var, bg="#f5f5f5")
            cb.pack(side="left", anchor="n", pady=2)
            
            # Text container
            text_frame = tk.Frame(frame, bg="#f5f5f5")
            text_frame.pack(side="left", fill="x", expand=True)
            
            # Title (bigger)
            tk.Label(text_frame, text=item, font=("Arial", 10, "bold"), bg="#f5f5f5", anchor="w").pack(anchor="w")
            # Hint underneath
            tk.Label(text_frame, text=hint, font=("Arial", 8), fg="#666", bg="#f5f5f5", anchor="w").pack(anchor="w")'''

content = content.replace(old_rendering, new_rendering)

with open('trading_journal_final.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Checklist styling updated:")
print("- Headers bigger (10pt bold)")
print("- Subtext underneath each title")
print("- Better spacing")
