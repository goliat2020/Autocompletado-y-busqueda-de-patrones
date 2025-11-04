import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import time

try:
    import algorithms
    algorithms_available = True
except Exception:
    algorithms = None
    algorithms_available = False


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("LECTOR DE TEXTOS")

        top = tk.Frame(root)
        top.pack(fill="x", padx=8, pady=8)

        btn_open = tk.Button(top, text="Open file", command=self.open_file)
        btn_open.pack(side="left")

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.word_search)
        self.search_entry = tk.Entry(top, textvariable=self.search_var, width=30)
        self.search_entry.pack(side="right")

        self.lbl_file = tk.Label(top, text="No file loaded")
        self.lbl_file.pack(side="left", padx=8)

        self.status = tk.Label(root, text="", anchor="w")
        self.status.pack(fill="x", padx=8)

        self.suggestion_box = tk.Listbox(root, height=6)
        self.suggestion_box.bind("<<ListboxSelect>>", self.on_suggestion_select)
        self.suggestions_visible = False

        self.text_widget = scrolledtext.ScrolledText(root, wrap="word", width=100, height=30)
        self.text_widget.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.text = ""
        self.lower_text = ""
        self.byte_to_char = None

        self.text_widget.tag_configure("match", background="yellow")

    def open_file(self):
        fn = filedialog.askopenfilename(title="Open text file",
                                        filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not fn:
            return
        try:
            with open(fn, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")
            return

        self.text = content
        self.lower_text = content.lower()

        lb = self.lower_text.encode('utf-8')
        if lb:
            b2c = [0] * (len(lb) + 1)
            byte_index = 0
            char_index = 0
            for ch in self.lower_text:
                b = ch.encode('utf-8')
                for _ in range(len(b)):
                    if byte_index < len(b2c):
                        b2c[byte_index] = char_index
                    byte_index += 1
                char_index += 1
            if byte_index <= len(b2c) - 1:
                b2c[byte_index] = char_index
            self.byte_to_char = b2c
        else:
            self.byte_to_char = [0]

        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert(tk.END, content)
        self.lbl_file.config(text=fn)
        self.status.config(text=f"Loaded {len(content)} characters")

        if algorithms_available:
            try:
                algorithms.read_file(fn)
                algorithms.createTrie()
            except Exception as e:
                messagebox.showwarning("Warning", f"Could not build C++ trie:\n{e}")

        self.text_widget.tag_remove("match", "1.0", tk.END)

    def clear_highlights(self):
        self.text_widget.tag_remove("match", "1.0", tk.END)

    def highlight_matches(self, matches, query_len):
        self.clear_highlights()
        for pos in matches[:1000]:
            # print(pos)
            start = f"1.0+{pos}c"
            end = f"1.0+{pos + query_len}c"
            try:
                self.text_widget.tag_add("match", start, end)
            except tk.TclError:
                pass
        if matches:
            first = matches[0]
            index = f"1.0+{first}c"
            self.text_widget.see(index)

    def show_suggestions(self, suggestions):
        if not suggestions:
            if self.suggestions_visible:
                self.suggestion_box.pack_forget()
                self.suggestions_visible = False
            return
        self.suggestion_box.delete(0, tk.END)
        for s in suggestions:
            self.suggestion_box.insert(tk.END, s)
        if not self.suggestions_visible:
            self.text_widget.pack_forget()
            self.suggestion_box.pack(fill="x", padx=8)
            self.text_widget.pack(fill="both", expand=True, padx=8, pady=(0, 8))
            self.suggestions_visible = True

    def on_suggestion_select(self, event):
        if not self.suggestions_visible:
            return
        sel = self.suggestion_box.curselection()
        if not sel:
            return
        value = self.suggestion_box.get(sel[0])
        self.search_var.set(value)
        self.suggestion_box.pack_forget()
        self.suggestions_visible = False
        self.word_search()

    def word_search(self, *args):
        query = self.search_var.get()
        self.clear_highlights()
        if not query:
            self.status.config(text="")
            return
        if not self.text:
            self.status.config(text="No file loaded")
            return

        q_lower = query.lower()

        try:
            if algorithms_available:
                start_time1 = time.perf_counter()
                byte_matches = algorithms.kmp_search(q_lower, self.lower_text)
                end_time1 = time.perf_counter()
                duration_ms1 = (end_time1 - start_time1) * 1000
                print(f" KMP search response(ms): ", duration_ms1)
                if self.byte_to_char:
                    matches = [self.byte_to_char[b] if 0 <= b < len(self.byte_to_char) else len(self.lower_text)
                               for b in byte_matches]
                else:
                    matches = [len(self.lower_text.encode('utf-8')[:b].decode('utf-8')) for b in byte_matches]
                try:
                    start_time2 = time.perf_counter()
                    suggestions = algorithms.autocomplete(q_lower)
                    end_time2 = time.perf_counter()
                    duration_ms2 = (end_time2 - start_time2) * 1000
                    print(f" Autocomplete response(ms): ", duration_ms2)

                except Exception:
                    suggestions = []
            else:
                matches = []
                start = 0
                while True:
                    idx = self.lower_text.find(q_lower, start)
                    if idx == -1:
                        break
                    matches.append(idx)
                    start = idx + 1
        except Exception as e:
            messagebox.showerror("Search error", f"Error during search:\n{e}")
            return

        self.status.config(text=f"Matches: {len(matches)}")
        if matches:
            self.highlight_matches(matches, len(query))
        if algorithms_available:
            self.show_suggestions(suggestions)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
