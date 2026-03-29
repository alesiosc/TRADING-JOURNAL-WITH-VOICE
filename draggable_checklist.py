"""
Add drag-and-drop reordering to checklist
"""

import tkinter as tk
from tkinter import ttk

class DraggableChecklistItem(tk.Frame):
    def __init__(self, parent, item_name, hint, var, **kwargs):
        super().__init__(parent, **kwargs)
        self.item_name = item_name
        self.var = var
        self.parent_list = parent
        
        # Drag handle - aligned with checkbox
        self.drag_handle = tk.Label(self, text="☰", font=("Arial", 12), bg=kwargs.get('bg', '#f5f5f5'), cursor="hand2")
        self.drag_handle.pack(side="left", padx=(0, 5), pady=0)
        
        # Checkbox with green checkmark
        cb = tk.Checkbutton(self, variable=var, bg=kwargs.get('bg', '#f5f5f5'),
                           selectcolor='#f5f5f5', activebackground=kwargs.get('bg', '#f5f5f5'),
                           fg='#00FF00', activeforeground='#00FF00', font=("Arial", 12),
                           command=self.on_check)
        cb.pack(side="left", anchor="n", pady=0)
        
        # Text container
        text_frame = tk.Frame(self, bg=kwargs.get('bg', '#f5f5f5'))
        text_frame.pack(side="left", fill="x", expand=True)
        
        # Title
        tk.Label(text_frame, text=item_name, font=("Arial", 10, "bold"), bg=kwargs.get('bg', '#f5f5f5'), anchor="w").pack(anchor="w")
        # Hint
        tk.Label(text_frame, text=hint, font=("Arial", 8), fg="#666", bg=kwargs.get('bg', '#f5f5f5'), anchor="w").pack(anchor="w")
        
        # Bind drag events
        self.drag_handle.bind("<Button-1>", self.start_drag)
        self.drag_handle.bind("<B1-Motion>", self.on_drag)
        self.drag_handle.bind("<ButtonRelease-1>", self.end_drag)
        
        self.drag_start_y = 0
        self.original_index = 0
    
    def on_check(self):
        # Hide drag handle when checked
        if self.var.get():
            self.drag_handle.config(text="")
        else:
            self.drag_handle.config(text="☰")    
    def start_drag(self, event):
        self.drag_start_y = event.y_root
        self.original_index = self.parent_list.items.index(self)
        self.config(relief="raised", borderwidth=2)
    
    def on_drag(self, event):
        delta_y = event.y_root - self.drag_start_y
        
        # Calculate new position
        current_index = self.parent_list.items.index(self)
        items = self.parent_list.items
        
        if delta_y < -20 and current_index > 0:
            # Move up
            items[current_index], items[current_index - 1] = items[current_index - 1], items[current_index]
            self.parent_list.repack_items()
            self.drag_start_y = event.y_root
        elif delta_y > 20 and current_index < len(items) - 1:
            # Move down
            items[current_index], items[current_index + 1] = items[current_index + 1], items[current_index]
            self.parent_list.repack_items()
            self.drag_start_y = event.y_root
    
    def end_drag(self, event):
        self.config(relief="flat", borderwidth=0)

class DraggableChecklist(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.items = []
    
    def add_item(self, item_name, hint, var):
        item = DraggableChecklistItem(self, item_name, hint, var, bg=self.cget('bg'))
        item.pack(fill="x", padx=10, pady=4)
        self.items.append(item)
        return item
    
    def repack_items(self):
        for item in self.items:
            item.pack_forget()
        for item in self.items:
            item.pack(fill="x", padx=10, pady=4)
    
    def get_order(self):
        return [item.item_name for item in self.items]

if __name__ == "__main__":
    print("Draggable checklist component created")
    print("Use drag handle (☰) to reorder items")
