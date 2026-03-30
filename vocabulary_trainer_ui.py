import tkinter as tk
from tkinter import ttk, messagebox
import vocabulary_trainer as vt

class VocabularyTrainerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Vocabulary Trainer")
        self.root.geometry("900x700")
        
        canvas = tk.Canvas(root)
        scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, padx=20, pady=20)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        main_frame = scrollable_frame
        
        tk.Label(main_frame, text="Vocabulary Trainer", font=("Arial", 16, "bold")).pack(pady=(0, 5))
        tk.Label(main_frame, text="Syncing with Notion...", font=("Arial", 9), fg="#999").pack()
        
        vt.sync_vocab_with_notion()
        
        tk.Label(main_frame, text="Unknown Phrases", font=("Arial", 14, "bold")).pack(pady=(10, 5))
        instructions = "Review and categorize unknown phrases from your voice transcripts."
        tk.Label(main_frame, text=instructions, font=("Arial", 10), fg="#666").pack(pady=(0, 20))
        
        self.unknown_phrases = vt.get_unknown_phrases()
        if not self.unknown_phrases:
            tk.Label(main_frame, text="No unknown phrases to review!", font=("Arial", 12), fg="green").pack(pady=50)
            tk.Button(main_frame, text="Close", command=root.destroy, font=("Arial", 10)).pack()
            return
        
        self.current_index = 0
        phrase_frame = tk.Frame(main_frame, bg="#f0f0f0", relief="solid", bd=2, padx=20, pady=20)
        phrase_frame.pack(fill="x", pady=(0, 20))
        tk.Label(phrase_frame, text="Phrase:", font=("Arial", 10), bg="#f0f0f0").pack()
        self.phrase_text = tk.Text(phrase_frame, height=2, font=("Arial", 14, "bold"), bg="#f0f0f0", fg="#1976d2", wrap="word", relief="flat", cursor="xterm")
        self.phrase_text.pack(pady=10, fill="x")
        self.counter_label = tk.Label(phrase_frame, text="", font=("Arial", 9), bg="#f0f0f0", fg="#666")
        self.counter_label.pack()
        
        # All buttons above column selection
        all_buttons_frame = tk.Frame(main_frame)
        all_buttons_frame.pack(pady=15)
        tk.Button(all_buttons_frame, text="← Back", command=self.go_back, font=("Arial", 10), bg="#607D8B", fg="white", padx=20, pady=5).pack(side="left", padx=5)
        tk.Button(all_buttons_frame, text="🗑 Delete Phrase", command=self.delete_phrase, font=("Arial", 10), bg="#F44336", fg="white", padx=20, pady=5).pack(side="left", padx=5)
        tk.Button(all_buttons_frame, text="Skip", command=self.skip_phrase, font=("Arial", 10), bg="#999", fg="white", padx=20, pady=5).pack(side="left", padx=5)
        tk.Button(all_buttons_frame, text="Save and Next", command=self.save_phrase, font=("Arial", 10), bg="#4CAF50", fg="white", padx=20, pady=5).pack(side="left", padx=5)
        tk.Button(all_buttons_frame, text="Finish", command=self.finish, font=("Arial", 10), bg="#2196F3", fg="white", padx=20, pady=5).pack(side="left", padx=5)
        
        # Two-column layout for Column selection and Value selection
        selection_container = tk.Frame(main_frame)
        selection_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left column: Select Notion Column
        left_column = tk.Frame(selection_container)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        tk.Label(left_column, text="Select Notion Column:", font=("Arial", 11, "bold")).pack(pady=(0, 5))
        self.category_var = tk.StringVar()
        
        notion_columns = vt.get_notion_columns()
        self.category_mapping = {}
        for col_key, col_info in notion_columns.items():
            self.category_mapping[col_info['display_name']] = col_key
        
        category_frame = tk.Frame(left_column)
        category_frame.pack(fill="both", expand=True)
        
        if not self.category_mapping:
            tk.Label(category_frame, text="No Notion columns found!", fg="red").pack()
        else:
            # Maintain Notion order
            for col_key, col_info in notion_columns.items():
                display_name = col_info['display_name']
                tk.Radiobutton(category_frame, text=display_name, variable=self.category_var, value=display_name, font=("Arial", 10)).pack(anchor="w", pady=2)
        
        # Right column: Select Value
        right_column = tk.Frame(selection_container)
        right_column.pack(side="left", fill="both", expand=True, padx=(10, 0))
        
        tk.Label(right_column, text="Select Value:", font=("Arial", 11, "bold")).pack(pady=(0, 5))
        self.value_var = tk.StringVar()
        value_container = tk.Frame(right_column)
        value_container.pack(fill="both", expand=True)
        value_canvas = tk.Canvas(value_container, height=200)
        value_scrollbar = tk.Scrollbar(value_container, orient="vertical", command=value_canvas.yview)
        self.value_frame = tk.Frame(value_canvas)
        self.value_frame.bind("<Configure>", lambda e: value_canvas.configure(scrollregion=value_canvas.bbox("all")))
        value_canvas.create_window((0, 0), window=self.value_frame, anchor="nw")
        value_canvas.configure(yscrollcommand=value_scrollbar.set)
        value_canvas.pack(side="left", fill="both", expand=True)
        value_scrollbar.pack(side="right", fill="y")
        self.category_var.trace("w", self.update_values)
        
        self.display_current_phrase()
    
    def update_values(self, *args):
        for widget in self.value_frame.winfo_children():
            widget.destroy()
        display_name = self.category_var.get()
        if not display_name:
            return
        category = self.category_mapping.get(display_name)
        if not category:
            return
        vocab = vt.load_vocab()
        if category in vocab:
            values = list(vocab[category].keys())
            for val in values:
                tk.Radiobutton(self.value_frame, text=val, variable=self.value_var, value=val, font=("Arial", 10)).pack(anchor="w", pady=2)
    
    def display_current_phrase(self):
        if self.current_index < len(self.unknown_phrases):
            phrase = self.unknown_phrases[self.current_index]
            self.phrase_text.config(state="normal")
            self.phrase_text.delete("1.0", "end")
            self.phrase_text.insert("1.0", '"{}"'.format(phrase))
            self.phrase_text.config(state="normal")
            self.counter_label.config(text="Phrase {} of {}".format(self.current_index + 1, len(self.unknown_phrases)))
        else:
            self.finish()
    
    def save_phrase(self):
        display_name = self.category_var.get()
        value = self.value_var.get()
        if not display_name or not value:
            messagebox.showwarning("Missing Selection", "Please select both column and value")
            return
        category = self.category_mapping.get(display_name)
        if not category:
            messagebox.showerror("Error", "Invalid category selected")
            return
        phrase = self.unknown_phrases[self.current_index]
        if vt.add_phrase(category, value, phrase):
            vocab = vt.load_vocab()
            if phrase.lower() in vocab["unknown_phrases"]:
                vocab["unknown_phrases"].remove(phrase.lower())
            vt.save_vocab(vocab)
            self.current_index += 1
            self.category_var.set("")
            self.value_var.set("")
            self.display_current_phrase()
        else:
            messagebox.showerror("Error", "Failed to save phrase")
    
    def skip_phrase(self):
        self.current_index += 1
        self.category_var.set("")
        self.value_var.set("")
        self.display_current_phrase()
    
    def go_back(self):
        """Go back to previous phrase"""
        if self.current_index > 0:
            self.current_index -= 1
            self.category_var.set("")
            self.value_var.set("")
            self.display_current_phrase()
        else:
            messagebox.showinfo("First Phrase", "Already at the first phrase")
    
    def delete_phrase(self):
        """Delete current phrase from unknown phrases list"""
        if messagebox.askyesno("Delete Phrase", "Delete this phrase permanently?"):
            phrase = self.unknown_phrases[self.current_index]
            vocab = vt.load_vocab()
            if phrase.lower() in vocab["unknown_phrases"]:
                vocab["unknown_phrases"].remove(phrase.lower())
                vt.save_vocab(vocab)
            
            # Remove from current list
            self.unknown_phrases.pop(self.current_index)
            
            # Adjust index if needed
            if self.current_index >= len(self.unknown_phrases):
                self.current_index = max(0, len(self.unknown_phrases) - 1)
            
            self.category_var.set("")
            self.value_var.set("")
            
            if len(self.unknown_phrases) == 0:
                messagebox.showinfo("Complete", "All phrases reviewed!")
                self.root.destroy()
            else:
                self.display_current_phrase()
    
    def finish(self):
        messagebox.showinfo("Complete", "Vocabulary training session finished!")
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = VocabularyTrainerUI(root)
    root.mainloop()