
import sys
import os

# Add both current dir (routers) and project root to sys.path so it works however it is executed
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
for path in (CURRENT_DIR, PROJECT_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

import tkinter as tk
from tkinter import messagebox
import requests
import threading
import time
from datetime import datetime
from pynput import mouse, keyboard

try:
    from routers.desktop_app.blackscreen import BlackScreen
except ImportError:
    from desktop_app.blackscreen import BlackScreen

API_URL = "http://127.0.0.1:8000"
IDLE_THRESHOLD = 30


class EmployeeDashboard:

    def __init__(self):
        self.root = tk.Tk()
        self.black = BlackScreen(self.root, on_activity=self.mark_input)
        
        self.root.title("Employee Attendance")
        self.root.geometry("420x360")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.user_id = None
        self.logged_in = False
        self.login_time = None
        self.last_input = None
        self.idle_started = None

        self.total_idle = 0.0
        self.total_working = 0.0
        self.day_key = None

        self.mouse_listener = None
        self.keyboard_listener = None

        self.show_login()
        self.root.mainloop()

    def on_close(self):
        self.logged_in = False
        self.stop_input_listeners()
        self.black.hide()
        self.root.destroy()
        

    # ---------------- LOGIN SCREEN ----------------

    def show_login(self):
        self.clear_screen()

        tk.Label(
            self.root,
            text="Employee Login",
            font=("Arial", 22, "bold")
        ).pack(pady=25)

        tk.Label(self.root, text="User ID").pack()

        self.user_entry = tk.Entry(
            self.root, font=("Arial", 12), width=28
        )
        self.user_entry.pack(pady=7)

        tk.Label(self.root, text="Password").pack()

        self.password_entry = tk.Entry(
            self.root, font=("Arial", 12),
            width=28, show="*"
        )
        self.password_entry.pack(pady=7)

        self.login_button = tk.Button(
            self.root,
            text="LOGIN",
            width=20,
            command=self.login
        )
        self.login_button.pack(pady=15)

        self.status_label = tk.Label(
            self.root, text="Enter your login details"
        )
        self.status_label.pack()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def login(self):
        user_id = self.user_entry.get().strip()
        password = self.password_entry.get()

        if not user_id or not password:
            messagebox.showwarning(
                "Missing Details",
                "Enter User ID and Password."
            )
            return

        self.login_button.config(
            state="disabled", text="Checking..."
        )

        threading.Thread(
            target=self.check_login,
            args=(user_id, password),
            daemon=True
        ).start()

    def check_login(self, user_id, password):
        try:
            response = requests.post(
                f"{API_URL}/login",
                json={
                    "user_id": user_id,
                    "password": password
                },
                timeout=10
            )

            print("LOGIN STATUS:", response.status_code)
            print("BACKEND RESPONSE:", response.text)

            if response.status_code == 200:
                data = response.json()

                if data.get("success") is True:
                    self.root.after(
                        0, lambda: self.login_success(user_id)
                    )
                else:
                    self.root.after(
                        0,
                        lambda: self.login_failed(
                            data.get("message", "Login failed")
                        )
                    )

            elif response.status_code == 401:
                self.root.after(
                    0,
                    lambda: self.login_failed(
                        "Invalid User ID or Password."
                    )
                )
            else:
                error = (
                    f"HTTP {response.status_code}\n"
                    f"{response.text[:300]}"
                )
                self.root.after(
                    0, lambda: self.login_failed(error)
                )

        except requests.exceptions.ConnectionError:
            self.root.after(
                0,
                lambda: self.login_failed(
                    "Cannot connect to backend. "
                    "Check that Uvicorn is running."
                )
            )

        except requests.exceptions.Timeout:
            self.root.after(
                0,
                lambda: self.login_failed(
                    "Backend request timed out."
                )
            )

        except Exception as exc:
            error = str(exc)
            self.root.after(
                0, lambda: self.login_failed(error)
            )

    def login_failed(self, message):
        self.login_button.config(
            state="normal", text="LOGIN"
        )
        messagebox.showerror("Login Failed", message)

    # ---------------- TIME DASHBOARD ----------------

    def login_success(self, user_id):
        self.user_id = user_id
        self.logged_in = True

        self.login_time = time.monotonic()
        self.last_input = self.login_time
        self.idle_started = None

        self.total_idle = 0.0
        self.total_working = 0.0
        self.day_key = datetime.now().date()

        self.show_time_dashboard()
        self.start_input_listeners()
        self.update_times()

        # Save Attendance IN to database
        threading.Thread(
            target=self.save_login,
            args=(self.user_id,),
            daemon=True
        ).start()

    def show_time_dashboard(self):
        self.clear_screen()

        tk.Label(
            self.root,
            text=f"Employee: {self.user_id}",
            font=("Arial", 16, "bold")
        ).pack(pady=(15, 5))

        self.status_label = tk.Label(
            self.root,
            text="Status: Working",
            font=("Arial", 12)
        )
        self.status_label.pack(pady=5)

        self.overall_label = tk.Label(
            self.root,
            text="Overall Time: 00:00:00",
            font=("Arial", 13)
        )
        self.overall_label.pack(pady=8)

        self.working_label = tk.Label(
            self.root,
            text="Working Time: 00:00:00",
            font=("Arial", 13)
        )
        self.working_label.pack(pady=8)

        self.idle_label = tk.Label(
            self.root,
            text="Idle Time: 00:00:00",
            font=("Arial", 13)
        )
        self.idle_label.pack(pady=8)

        tk.Button(
            self.root,
            text="LOGOUT",
            width=20,
            command=self.logout
        ).pack(pady=18)

    # ---------------- INPUT MONITORING ----------------

    def mark_input(self, *args):
        if self.logged_in:
            self.last_input = time.monotonic()
            if self.idle_started is not None:
                try:
                    self.root.after(0, self.update_times)
                except Exception:
                    pass

    def start_input_listeners(self):
        self.stop_input_listeners()
        self.mouse_listener = mouse.Listener(
            on_move=self.mark_input,
            on_click=self.mark_input,
            on_scroll=self.mark_input
        )

        self.keyboard_listener = keyboard.Listener(
            on_press=self.mark_input
        )

        self.mouse_listener.start()
        self.keyboard_listener.start()

    def stop_input_listeners(self):
        if self.mouse_listener:
            try:
                self.mouse_listener.stop()
            except Exception:
                pass
            self.mouse_listener = None

        if self.keyboard_listener:
            try:
                self.keyboard_listener.stop()
            except Exception:
                pass
            self.keyboard_listener = None

    # ---------------- CALCULATE TIME ----------------

    def format_time(self, seconds):
        seconds = max(0, int(seconds))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        return f"{hours:02}:{minutes:02}:{secs:02}"

    def update_times(self):
        if not self.logged_in:
            return

        now = time.monotonic()
        overall = now - self.login_time
        inactive = now - self.last_input

        if inactive >= IDLE_THRESHOLD:
            if self.idle_started is None:
                self.idle_started = self.last_input
                self.black.show(
                    IDLE_THRESHOLD,
                    start_time=self.idle_started
                )

            current_idle = now - self.idle_started
            idle_seconds = (
                self.total_idle
                + max(0, current_idle)
            )
            status = "Idle"
        else:
            if self.idle_started is not None:
                completed_idle = now - self.idle_started
                self.total_idle += max(0, completed_idle)
                self.idle_started = None
                self.black.hide()

            idle_seconds = self.total_idle
            status = "Working"

        working_seconds = max(0, overall - idle_seconds)

        self.status_label.config(text=f"Status: {status}")
        self.overall_label.config(text=f"Overall Time: {self.format_time(overall)}")
        self.working_label.config(text=f"Working Time: {self.format_time(working_seconds)}")
        self.idle_label.config(text=f"Idle Time: {self.format_time(idle_seconds)}")

        self.root.after(500, self.update_times)

    # ---------------- LOGOUT ----------------

    def logout(self):
        if not self.logged_in:
            return

        overall = time.monotonic() - self.login_time
        now = time.monotonic()

        if self.idle_started is not None:
            self.total_idle += max(0, now - self.idle_started)
            self.idle_started = None

        self.black.hide()

        idle_seconds = self.total_idle
        working_seconds = max(0, overall - idle_seconds)

        self.logged_in = False
        self.stop_input_listeners()

        print("Employee:", self.user_id)
        print("Overall seconds:", int(overall))
        print("Working seconds:", int(working_seconds))
        print("Idle seconds:", int(idle_seconds))

        idle_minutes = round(idle_seconds / 60, 2)

        # Saves attendance OUT with idle time to database
        threading.Thread(
            target=self.save_logout,
            args=(self.user_id, idle_minutes),
            daemon=True
        ).start()

        messagebox.showinfo(
            "Session Summary",
            f"Overall Time: {self.format_time(overall)}\n"
            f"Working Time: {self.format_time(working_seconds)}\n"
            f"Idle Time: {self.format_time(idle_seconds)}"
        )

        self.show_login()


    def save_login(self, user_id):
        try:
            response = requests.post(
                f"{API_URL}/attendance/in",
                params={"user_id": user_id},
                timeout=10
            )
            print("ATTENDANCE IN STATUS:", response.status_code)
            print("ATTENDANCE IN RESPONSE:", response.text)
        except requests.RequestException as exc:
            print("Attendance IN API error:", exc)

    def save_logout(self, user_id, idle_minutes=0.0):
        try:
            response = requests.post(
                f"{API_URL}/attendance/out",
                params={
                    "user_id": user_id,
                    "idle_time_minutes": idle_minutes
                },
                timeout=10
            )

            print("LOGOUT STATUS:", response.status_code)
            print("LOGOUT RESPONSE:", response.text)

        except requests.RequestException as exc:
            print("Attendance logout API error:", exc)


if __name__ == "__main__":
    EmployeeDashboard()
