
import tkinter as tk
import time


class BlackScreen:
    def __init__(self, parent=None, on_activity=None):
        self.parent = parent
        self.on_activity = on_activity
        self.window = None
        self.timer_label = None
        self.started_at = None
        self.timer_job = None

    def show(self, idle_threshold=30, start_time=None):
        # Already open irundha marubadi create panna vendam
        if self.window and self.window.winfo_exists():
            return

        self.started_at = start_time if start_time is not None else time.monotonic()

        self.window = tk.Toplevel(self.parent) if self.parent else tk.Toplevel()
        self.window.configure(bg="black")
        self.window.title("Idle Screen")

        # Full screen occupy pannum & stay on top
        self.window.attributes("-fullscreen", True)
        self.window.attributes("-topmost", True)
        self.window.configure(cursor="none")

        # Alt+F4 use panni accidentally close aagama
        self.window.protocol("WM_DELETE_WINDOW", self.hide)

        # Catch user input inside black screen window as well
        if self.on_activity:
            self.window.bind("<Any-KeyPress>", lambda e: self.on_activity())
            self.window.bind("<Motion>", lambda e: self.on_activity())
            self.window.bind("<Button>", lambda e: self.on_activity())

        self.timer_label = tk.Label(
            self.window,
            text="IDLE TIME\n\n00:00",
            font=("Arial", 36, "bold"),
            fg="white",
            bg="black"
        )
        self.timer_label.pack(expand=True)

        self.window.update_idletasks()
        self.window.lift()
        self.window.focus_force()

        self.update_timer()

    def update_timer(self):
        if not self.window or not self.window.winfo_exists():
            return

        elapsed = max(0, int(time.monotonic() - self.started_at))
        minutes, seconds = divmod(elapsed, 60)

        try:
            self.timer_label.config(
                text=f"IDLE TIME\n\n{minutes:02d}:{seconds:02d}"
            )
            self.timer_job = self.window.after(1000, self.update_timer)
        except tk.TclError:
            pass

    def hide(self):
        if self.window:
            try:
                if self.timer_job:
                    self.window.after_cancel(self.timer_job)
            except (tk.TclError, AttributeError):
                pass

            try:
                self.window.destroy()
            except (tk.TclError, AttributeError):
                pass

        self.window = None
        self.timer_label = None
        self.timer_job = None
        self.started_at = None
