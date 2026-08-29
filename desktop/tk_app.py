import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from collector.core import full_report

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('NetHack — Authorized Network Diagnostics')
        self.geometry('980x700')
        self.report = None
        top = ttk.Frame(self, padding=10); top.pack(fill='x')
        ttk.Label(top, text='Target (authorized):').pack(side='left')
        self.target = ttk.Entry(top, width=32); self.target.pack(side='left', padx=6)
        ttk.Label(top, text='TCP port:').pack(side='left')
        self.port = ttk.Entry(top, width=8); self.port.insert(0, '443'); self.port.pack(side='left', padx=6)
        ttk.Button(top, text='Run diagnostics', command=self.run).pack(side='left', padx=6)
        ttk.Button(top, text='Export JSON', command=self.export).pack(side='left')
        self.text = tk.Text(self, wrap='none', font=('Menlo', 11)); self.text.pack(fill='both', expand=True, padx=10, pady=10)
        self.text.insert('1.0', 'Use this program only on systems/networks you own or administer.\n')
    def run(self):
        try:
            target = self.target.get().strip() or None
            port = int(self.port.get()) if self.port.get().strip() else None
            self.report = full_report(target, port)
            self.text.delete('1.0','end')
            self.text.insert('1.0', json.dumps(self.report, ensure_ascii=False, indent=2))
        except Exception as e:
            messagebox.showerror('NetHack', str(e))
    def export(self):
        if not self.report:
            return
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON','*.json')])
        if path:
            Path(path).write_text(json.dumps(self.report, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__':
    App().mainloop()
