
import os
import sys
import time
import threading
import tkinter as tk
from datetime import datetime

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_ROUTERS_DIR = os.path.dirname(_CURRENT_DIR)
_PROJECT_ROOT = os.path.dirname(_ROUTERS_DIR)
for _p in (_CURRENT_DIR, _ROUTERS_DIR, _PROJECT_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import requests
from pynput import mouse, keyboard
from dotenv import load_dotenv

try:
    from routers.desktop_app.blackscreen import BlackScreen
except ImportError:
    from desktop_app.blackscreen import BlackScreen

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")





IDLE_THRESHOLD = 30


def send_event(user_id, activity, idle_seconds=0):
    payload = {
        "user_id": user_id,
        "activity": activity,
    }

    if activity == "IDLE_START":
        payload["idle_reason"] = "No mouse/keyboard input"

    if activity == "RESUME":
        payload["idle_minutes"] = round(idle_seconds / 60, 2)

    try:
        response = requests.post(
            f"{API_URL}/monitoring/event",
            json=payload,
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print("Monitoring API error:", exc)

    try:
        response = requests.post(
            f"{API_URL}/attendance/in",
            json=payload,
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print("Attendance API error:", exc)


class MonitorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Staff Monitor")
        self.root.geometry("320x120")

        self.status = tk.Label(
            self.root, text="Working", font=("Arial", 14)
        )
        self.status.pack(pady=20)

        self.black = BlackScreen(self.root)
        self.last_input = time.monotonic()
        self.idle_started = None
        self.closed = False

        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse,
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll,
        )
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key,
        )

        self.mouse_listener.start()
        self.keyboard_listener.start()

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(500, self.check_idle)

    def mark_input(self):
        self.last_input = time.monotonic()

    def on_mouse(self, x, y):
        self.mark_input()

    def on_mouse_click(self, x, y, button, pressed):
        if pressed:
            self.mark_input()

    def on_mouse_scroll(self, x, y, dx, dy):
        self.mark_input()

    def on_key(self, key):
        self.mark_input()

    def check_idle(self):
        if self.closed:
            return

        now = time.monotonic()
        inactive = now - self.last_input

        if self.idle_started is None and inactive >= IDLE_THRESHOLD:
            self.idle_started = now
            self.status.config(text="Idle")
            self.black.show(IDLE_THRESHOLD)

            threading.Thread(
                target=send_event,
                args=("IDLE_START",),
                daemon=True,
            ).start()

        elif self.idle_started is not None:
            # Resume as soon as new input is detected.
            if self.last_input > self.idle_started:
                duration = now - self.idle_started
                self.idle_started = None
                self.black.hide()
                self.status.config(text="Working")

                threading.Thread(
                    target=send_event,
                    args=("RESUME", duration),
                    daemon=True,
                ).start()

        self.root.after(500, self.check_idle)

    def close(self):
        self.closed = True
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        self.black.hide()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    MonitorApp().run()


