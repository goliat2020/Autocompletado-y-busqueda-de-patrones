import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# Try to import the pybind11-built extension. If it's not built yet, keep a fallback.
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

        # suggestion listbox (hidden until needed)
        self.suggestion_box = tk.Listbox(root, height=6)
        self.suggestion_box.bind("<<ListboxSelect>>", self.on_suggestion_select)
        self.suggestions_visible = False

        self.text_widget = scrolledtext.ScrolledText(root, wrap="word", width=100, height=30)
        self.text_widget.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # store the raw text and a lower-cased copy for case-insensitive search
        self.text = ""
        self.lower_text = ""
        # byte->char map for converting C++ byte offsets to Python character indices
        self.byte_to_char = None

        # tag used to highlight matches
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
        # keep a lower-cased copy so we can perform case-insensitive KMP without changing C++ logic
        self.lower_text = content.lower()

        # build byte->char map for UTF-8 conversion (only once per file)
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
            # final position maps to char_index
            if byte_index <= len(b2c) - 1:
                b2c[byte_index] = char_index
            self.byte_to_char = b2c
        else:
            self.byte_to_char = [0]

        # display
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert(tk.END, content)
        self.lbl_file.config(text=fn)
        self.status.config(text=f"Loaded {len(content)} characters")

        # populate C++ structures (uniqueWords / trie) so autocomplete works
        if algorithms_available:
            try:
                algorithms.read_file(fn)
                algorithms.createTrie()
            except Exception as e:
                # non-fatal: show a warning but continue
                messagebox.showwarning("Warning", f"Could not build C++ trie:\n{e}")

        # clear previous highlights
        self.text_widget.tag_remove("match", "1.0", tk.END)

    def clear_highlights(self):
        self.text_widget.tag_remove("match", "1.0", tk.END)

    def highlight_matches(self, matches, query_len):
        # add 'match' tag for each match position (limit to avoid UI freeze)
        self.clear_highlights()
        for pos in matches[:1000]:
            start = f"1.0+{pos}c"
            end = f"1.0+{pos + query_len}c"
            try:
                self.text_widget.tag_add("match", start, end)
            except tk.TclError:
                # ignore any invalid indices
                pass
        # scroll to first match if any
        if matches:
            first = matches[0]
            index = f"1.0+{first}c"
            self.text_widget.see(index)

    def show_suggestions(self, suggestions):
        # populate and show the suggestion box
        if not suggestions:
            if self.suggestions_visible:
                self.suggestion_box.pack_forget()
                self.suggestions_visible = False
            return
        # fill listbox
        self.suggestion_box.delete(0, tk.END)
        for s in suggestions:
            self.suggestion_box.insert(tk.END, s)
        # if not visible, pack it right above the text widget
        if not self.suggestions_visible:
            # temporarily remove and re-add text widget so suggestions appear above it
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
        # set the search entry to the selected suggestion and trigger search
        self.search_var.set(value)
        # hide suggestions
        self.suggestion_box.pack_forget()
        self.suggestions_visible = False
        # run search/highlight for the selected suggestion
        self.word_search()

    def word_search(self, *args):
        query = self.search_var.get()
        # clear old highlights right away
        self.clear_highlights()
        if not query:
            self.status.config(text="")
            return
        if not self.text:
            self.status.config(text="No file loaded")
            return

        # perform case-insensitive search by lowercasing query and searching in lower_text
        q_lower = query.lower()

        # call C++ KMP if available, otherwise use a simple Python fallback
        try:
            if algorithms_available:
                byte_matches = algorithms.kmp_search(q_lower, self.lower_text)
                # convert byte offsets -> character offsets using precomputed map
                if self.byte_to_char:
                    matches = [self.byte_to_char[b] if 0 <= b < len(self.byte_to_char) else len(self.lower_text)
                               for b in byte_matches]
                else:
                    # fallback conversion: decode prefix (slower)
                    matches = [len(self.lower_text.encode('utf-8')[:b].decode('utf-8')) for b in byte_matches]
                # also request autocomplete suggestions from the C++ trie
                try:
                    suggestions = algorithms.autocomplete(q_lower, 10)
                except Exception:
                    suggestions = []
            else:
                # fallback: find all occurrences using str.find
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
        # show suggestions (even if no matches)
        if algorithms_available:
            self.show_suggestions(suggestions)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
