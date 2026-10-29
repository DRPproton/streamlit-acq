"""Tkinter interface for step2_transfer.py. Run: python step2_app.py"""
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from step2_transfer import transfer


class Step2App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=20)
        self.pack(fill="both", expand=True)
        master.title("Step 2 | TRM to PsychoPy")
        master.geometry("820x650")
        master.minsize(650, 560)
        master.protocol("WM_DELETE_WINDOW", self.close)
        self.busy = False
        self.events = Queue()
        self.controls = []
        self.paths = {name: tk.StringVar() for name in ("trm", "psychopy", "output")}
        self.sheet = tk.StringVar(value="PsychoPy_R")
        self.suffix = tk.StringVar(value="7")
        self.include_c = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Select the two input workbooks to begin.")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(9, weight=1)
        ttk.Label(self, text="Transfer trial results", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
        ttk.Label(self, text="Match by image filename, Race, and Gender. Save results in a new workbook.").grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(0, 18))
        for row, (name, label) in enumerate((
            ("trm", "TRM workbook"), ("psychopy", "PsychoPy workbook"), ("output", "Save result as")
        ), start=2):
            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=7)
            entry = ttk.Entry(self, textvariable=self.paths[name])
            entry.grid(row=row, column=1, sticky="ew", pady=7)
            button = ttk.Button(self, text="Browse…", command=lambda n=name: self.browse(n))
            button.grid(row=row, column=2, padx=(8, 0), pady=7)
            self.controls.extend((entry, button))
        options = ttk.LabelFrame(self, text="Options", padding=12)
        options.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(12, 10))
        ttk.Label(options, text="PsychoPy sheet").grid(row=0, column=0, sticky="w")
        sheet_entry = ttk.Entry(options, textvariable=self.sheet, width=22)
        sheet_entry.grid(row=0, column=1, padx=10, sticky="w")
        checkbox = ttk.Checkbutton(options, text="Include C trials (ctrials)", variable=self.include_c)
        checkbox.grid(row=0, column=2, padx=12)
        ttk.Label(options, text="Image suffix length").grid(row=1, column=0, sticky="w", pady=(10, 0))
        spin = ttk.Spinbox(options, from_=0, to=1000, textvariable=self.suffix, width=8)
        spin.grid(row=1, column=1, sticky="w", padx=10, pady=(10, 0))
        ttk.Label(options, text="7 = notebook default; 0 = full source name").grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))
        self.controls.extend((sheet_entry, checkbox, spin))
        actions = ttk.Frame(self)
        actions.grid(row=6, column=0, columnspan=3, sticky="w", pady=8)
        for label, dry in (("Validate only", True), ("Run transfer", False)):
            button = ttk.Button(actions, text=label, command=lambda d=dry: self.start(d))
            button.pack(side="left", padx=(0, 10))
            self.controls.append(button)
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.grid(row=7, column=0, columnspan=3, sticky="ew", pady=6)
        ttk.Label(self, textvariable=self.status, wraplength=730).grid(
            row=8, column=0, columnspan=3, sticky="w", pady=8)
        self.log = ScrolledText(self, height=11, wrap="word", state="disabled", font=("Consolas", 10))
        self.log.grid(row=9, column=0, columnspan=3, sticky="nsew")
        ttk.Label(self, text="Existing files are never overwritten. Blank source responses retain existing values.",
                  wraplength=730).grid(row=10, column=0, columnspan=3, sticky="w", pady=(12, 0))
        self.after(100, self.poll)

    def browse(self, name):
        if name == "output":
            current = self.paths[name].get().strip()
            selected = filedialog.asksaveasfilename(
                parent=self, title="Save a new result workbook", defaultextension=".xlsx",
                filetypes=[("Excel workbook", "*.xlsx")],
                initialfile=Path(current).name if current else "PsychoPy_step2.xlsx")
        else:
            selected = filedialog.askopenfilename(
                parent=self, title=f"Select {name} workbook", filetypes=[("Excel workbook", "*.xlsx")])
        if selected:
            self.paths[name].set(selected)
            if name == "psychopy":
                path = Path(selected)
                self.paths["output"].set(str(path.with_name(path.stem + "_step2.xlsx")))

    def arguments(self, dry_run):
        values = {name: value.get().strip() for name, value in self.paths.items()}
        for name in ("trm", "psychopy"):
            if not values[name] or not Path(values[name]).is_file():
                raise ValueError(f"Select an existing {name} workbook.")
        if not values["output"]:
            path = Path(values["psychopy"])
            values["output"] = str(path.with_name(path.stem + "_step2.xlsx"))
            self.paths["output"].set(values["output"])
        sheet = self.sheet.get().strip()
        if not sheet:
            raise ValueError("Enter the PsychoPy sheet name.")
        try:
            suffix = int(self.suffix.get())
        except ValueError:
            raise ValueError("Image suffix length must be a whole number.") from None
        if suffix < 0:
            raise ValueError("Image suffix length cannot be negative.")
        return dict(**values, sheet=sheet, suffix_length=suffix,
                    include_ctrials=self.include_c.get(), dry_run=dry_run)

    def write_log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def start(self, dry_run):
        if self.busy:
            return
        try:
            args = self.arguments(dry_run)
        except ValueError as exc:
            messagebox.showerror("Check inputs", str(exc), parent=self)
            return
        self.busy = True
        for widget in self.controls:
            widget.state(["disabled"])
        self.progress.start(12)
        self.status.set("Validating…" if dry_run else "Transferring…")
        self.write_log(f"\n{'VALIDATE' if dry_run else 'TRANSFER'}\nTRM: {args['trm']}\nPsychoPy: {args['psychopy']}")
        Thread(target=self.work, args=(args,), daemon=True).start()

    def work(self, args):
        # Never access Tk objects from the worker thread.
        try:
            self.events.put(("success", args, transfer(**args)))
        except Exception as exc:
            self.events.put(("error", args, str(exc)))

    def poll(self):
        try:
            kind, args, result = self.events.get_nowait()
        except Empty:
            pass
        else:
            self.busy = False
            self.progress.stop()
            for widget in self.controls:
                widget.state(["!disabled"])
            if kind == "error":
                self.status.set("Transfer could not complete. See details below.")
                self.write_log("ERROR: " + result)
                messagebox.showerror("Transfer failed", result, parent=self)
            else:
                for sheet, counts in result.items():
                    verb = "would write" if args["dry_run"] else "wrote"
                    self.write_log(
                        f"{sheet}: {counts['matched_rows']} matched rows; "
                        f"{verb} {counts['cells_written']} cells; "
                        f"{counts['blank_values_skipped']} blanks retained; "
                        f"{counts['unused_source_rows']} unused source rows.")
                message = ("Validation passed. No file was written." if args["dry_run"]
                           else f"Saved: {Path(args['output']).resolve()}")
                self.status.set(message)
                self.write_log(message)
        self.after(100, self.poll)

    def close(self):
        if self.busy:
            messagebox.showinfo("Transfer in progress", "Wait for the current operation to finish.", parent=self)
            return
        self.master.destroy()


def main():
    root = tk.Tk()
    Step2App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
