
import tkinter as tk


class BlackScreen:
    def __init__(self, root):
        self.root = root
        self.window = None

    def show(self, idle_seconds=30):
        if self.window and self.window.winfo_exists():
            return

        self.window = tk.Toplevel(self.root)
        self.window.configure(bg="black")
        self.window.attributes("-fullscreen", True)
        self.window.attributes("-topmost", True)

        tk.Label(
            self.window,
            text="IDLE DETECTED",
            fg="white",
            bg="black",
            font=("Arial", 24),
        ).pack(expand=True)

        tk.Label(
            self.window,
            text=f"Idle threshold: {idle_seconds} seconds",
            fg="white",
            bg="black",
            font=("Arial", 12),
        ).pack(pady=30)

    def hide(self):
        if self.window and self.window.winfo_exists():
            self.window.destroy()
        self.window = None
