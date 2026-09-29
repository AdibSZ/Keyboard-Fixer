"""
Floating On-Screen Display (OSD) Toast Notification for Keyboard Fixer.
Displays a sleek, semi-transparent modern dark pill near the screen bottom-right
showing the converted snippet and target language, then fades away.
"""
import tkinter as tk
import customtkinter as ctk

class OSDToast:
    def __init__(self):
        self.toast_win = None
        self._hide_job = None

    def show(self, original_text: str, converted_text: str, target_lang: str):
        """Displays or updates the toast notification on screen."""
        try:
            if self.toast_win is None or not self.toast_win.winfo_exists():
                self.toast_win = tk.Toplevel()
                self.toast_win.overrideredirect(True)
                self.toast_win.attributes("-topmost", True)
                self.toast_win.attributes("-alpha", 0.95)

                self.frame = ctk.CTkFrame(
                    self.toast_win,
                    fg_color="#0f172a",
                    border_color="#38bdf8",
                    border_width=2,
                    corner_radius=12
                )
                self.frame.pack(fill="both", expand=True, padx=2, pady=2)

                self.header_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
                self.header_frame.pack(fill="x", padx=14, pady=(10, 4))

                self.app_lbl = ctk.CTkLabel(
                    self.header_frame,
                    text="⌨️ Keyboard Fixer",
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    text_color="#94a3b8"
                )
                self.app_lbl.pack(side="left")

                self.lang_badge = ctk.CTkLabel(
                    self.header_frame,
                    text="FA",
                    font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                    text_color="#ffffff",
                    fg_color="#10b981",
                    corner_radius=6,
                    padx=8,
                    pady=2
                )
                self.lang_badge.pack(side="right")

                self.text_lbl = ctk.CTkLabel(
                    self.frame,
                    text="",
                    font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                    text_color="#f8fafc",
                    wraplength=340,
                    justify="center"
                )
                self.text_lbl.pack(padx=16, pady=(4, 12))

            orig_disp = (original_text[:22] + "…") if len(original_text) > 22 else original_text
            conv_disp = (converted_text[:22] + "…") if len(converted_text) > 22 else converted_text

            self.text_lbl.configure(text=f"{orig_disp}   ➔   {conv_disp}")

            if target_lang == "fa":
                self.lang_badge.configure(text="Persian (FA)", fg_color="#10b981")
            else:
                self.lang_badge.configure(text="English (EN)", fg_color="#2563eb")

            self.toast_win.update_idletasks()
            w = self.toast_win.winfo_reqwidth()
            h = self.toast_win.winfo_reqheight()
            sw = self.toast_win.winfo_screenwidth()
            sh = self.toast_win.winfo_screenheight()

            x = sw - w - 24
            y = sh - h - 64
            self.toast_win.geometry(f"{w}x{h}+{x}+{y}")
            self.toast_win.deiconify()

            if self._hide_job:
                self.toast_win.after_cancel(self._hide_job)

            self._hide_job = self.toast_win.after(1600, self._hide)

        except Exception as e:
            print(f"[Toast] Error displaying toast: {e}")

    def _hide(self):
        try:
            if self.toast_win and self.toast_win.winfo_exists():
                self.toast_win.withdraw()
        except Exception:
            pass
