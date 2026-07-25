import json
import os
import sys
import threading
import time
import winreg

import customtkinter as ctk
import keyboard
import pyperclip
import pystray
from PIL import Image

# ==========================================
# 1. Setup & Dictionaries
# ==========================================
if "__compiled__" in globals():
    # برای فایل‌های کامپایل شده با Nuitka، مسیر واقعی فایل exe
    APP_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
    SCRIPT_DIR = APP_DIR
else:
    # برای زمانی که با پایتون اجرا می‌شود
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    SCRIPT_DIR = APP_DIR

CONFIG_FILE = os.path.join(APP_DIR, "config.json")
ICON_PATH = os.path.join(SCRIPT_DIR, "assets", "program.ico")

ENG_TO_FA = {
    'q': 'ض', 'w': 'ص', 'e': 'ث', 'r': 'ق', 't': 'ف', 'y': 'غ', 'u': 'ع', 'i': 'ه', 'o': 'خ', 'p': 'ح',
    '[': 'چ', ']': 'ج', '\\': 'پ',
    'a': 'ش', 's': 'س', 'd': 'ی', 'f': 'ب', 'g': 'ل', 'h': 'ا', 'j': 'ت', 'k': 'ن', 'l': 'م',
    ';': 'ک', "'": 'گ',
    'z': 'ظ', 'x': 'ط', 'c': 'ز', 'v': 'ر', 'b': 'ذ', 'n': 'د', 'm': 'ئ',
    ',': 'و', '.': '.', '/': '/',
    'Q': 'ً', 'W': 'ٌ', 'E': 'ٍ', 'R': 'ريال', 'T': '،', 'Y': '؛',
    'A': 'َ', 'S': 'ُ', 'D': 'ِ', 'F': 'ّ', 'G': 'ۀ', 'H': 'آ', 'J': 'ـ', 'K': '«', 'L': '»',
    ':': ':',
    'Z': 'ة', 'X': 'ي', 'C': 'ژ', 'V': 'ؤ', 'B': 'إ', 'N': 'أ', 'M': 'ء',
    '<': '<', '>': '>', '?': '؟',
}
FA_TO_ENG = {v: k for k, v in ENG_TO_FA.items()}

CURRENT_HOTKEY = "ctrl+alt+q"


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"hotkey": "ctrl+alt+q", "theme": "Dark", "auto_start": False}


def save_config(config: dict) -> None:
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f)


# ==========================================
# 2. Core Conversion Logic
# ==========================================
def convert_text(text: str, mapping: dict) -> str:
    return ''.join(mapping.get(char.lower(), char) for char in text)


def sanitize_hotkey(hotkey_str: str) -> str:
    parts = hotkey_str.split('+')
    clean_parts = []
    for p in parts:
        p = p.strip().lower()
        if p in FA_TO_ENG:
            clean_parts.append(FA_TO_ENG[p])
        else:
            clean_parts.append(p)
    return '+'.join(clean_parts)


def on_hotkey_press() -> None:
    try:
        keyboard.release('ctrl')
        keyboard.release('alt')
        keyboard.release('shift')

        time.sleep(0.1)
        pyperclip.copy('')

        keyboard.send('ctrl+c')
        time.sleep(0.2)

        text = pyperclip.paste()
        if not text:
            return

        last_key = CURRENT_HOTKEY.split('+')[-1].strip().lower()
        fa_last_key = ENG_TO_FA.get(last_key, "")

        if text.lower().startswith(last_key):
            text = text[1:]
        elif fa_last_key and text.startswith(fa_last_key):
            text = text[1:]

        if any(char in ENG_TO_FA for char in text.lower()):
            new_text = convert_text(text, ENG_TO_FA)
        else:
            new_text = convert_text(text, FA_TO_ENG)

        pyperclip.copy(new_text)
        time.sleep(0.1)

        keyboard.send('backspace')
        time.sleep(0.05)

        keyboard.send('ctrl+v')
    except Exception:
        pass


# ==========================================
# 3. Premium Modern UI (Rounded & Translucent)
# ==========================================
class SettingsApp(ctk.CTkToplevel):
    def __init__(self, master, config: dict):
        super().__init__(master)
        self.config_data = config
        self.new_hotkey = self.config_data["hotkey"]

        self.overrideredirect(True)
        self.wm_attributes("-alpha", "0.0")

        self.transparent_color = "#FF00FF"
        self.config(bg=self.transparent_color)
        self.wm_attributes("-transparentcolor", self.transparent_color)
        self.wm_attributes("-topmost", True)

        win_width, win_height = 420, 520
        x_pos = int(self.winfo_screenwidth() / 2 - win_width / 2)
        y_pos = int(self.winfo_screenheight() / 2 - win_height / 2)
        self.geometry(f"{win_width}x{win_height}+{x_pos}+{y_pos}")

        if os.path.exists(ICON_PATH):
            self.iconbitmap(ICON_PATH)

        self.alpha = 0.0

        self.build_ui()
        self.animate_fade_in()

    def build_ui(self) -> None:
        font_title = ctk.CTkFont(family="Segoe UI", size=22, weight="bold")
        font_subtitle = ctk.CTkFont(family="Segoe UI", size=12)
        font_label = ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
        font_btn = ctk.CTkFont(family="Segoe UI", size=15, weight="bold")
        font_small = ctk.CTkFont(family="Segoe UI", size=11)

        self.main_frame = ctk.CTkFrame(self, corner_radius=25, bg_color=self.transparent_color,
                                       fg_color=("#F3F3F3", "#1C1C1E"))
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        header = ctk.CTkFrame(self.main_frame, fg_color="transparent", corner_radius=0)
        header.pack(fill="x", padx=25, pady=(25, 0))

        ctk.CTkLabel(header, text="Keyboard Fixer", font=font_title,
                     text_color=("#1A1A1A", "#FFFFFF")).pack(side="left", anchor="w")

        ctk.CTkLabel(header, text="Premium Edition", font=font_subtitle,
                     text_color=("#8E8E93", "#98989F")).pack(side="left", anchor="w", padx=10, pady=(10, 0))

        ctk.CTkButton(header, text="✕", width=32, height=32, corner_radius=16,
                      fg_color="transparent", hover_color=("#FF3B30", "#FF453A"),
                      text_color=("#8E8E93", "#98989F"), font=font_btn,
                      command=self.animate_fade_out).pack(side="right", anchor="ne")

        body = ctk.CTkFrame(self.main_frame, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True, padx=25, pady=25)

        ctk.CTkLabel(body, text="HOTKEY", font=font_small,
                     text_color=("#8E8E93", "#98989F"), anchor="w").pack(fill="x", pady=(10, 5))

        self.hotkey_btn = ctk.CTkButton(body, text=self.config_data["hotkey"], font=font_btn,
                                        height=48, corner_radius=12,
                                        fg_color=("#FFFFFF", "#2C2C2E"),
                                        text_color=("#1A1A1A", "#FFFFFF"),
                                        border_width=2, border_color=("#007AFF", "#0A84FF"),
                                        hover_color=("#E5E5EA", "#3A3A3C"),
                                        command=self.start_listening_hotkey)
        self.hotkey_btn.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(body, text="Click the button and press your desired keys.", font=font_small,
                     text_color=("#8E8E93", "#98989F")).pack(fill="x", pady=(0, 25))

        ctk.CTkLabel(body, text="APPEARANCE", font=font_small,
                     text_color=("#8E8E93", "#98989F"), anchor="w").pack(fill="x", pady=(0, 5))
        self.theme_menu = ctk.CTkOptionMenu(body, values=["Dark", "Light", "System"],
                                            font=font_btn, height=48, corner_radius=12,
                                            fg_color=("#FFFFFF", "#2C2C2E"),
                                            button_color=("#007AFF", "#0A84FF"),
                                            button_hover_color=("#0062CC", "#1070FF"),
                                            text_color=("#1A1A1A", "#FFFFFF"),
                                            dropdown_fg_color=("#FFFFFF", "#2C2C2E"),
                                            command=self.change_theme)
        self.theme_menu.set(self.config_data["theme"])
        self.theme_menu.pack(fill="x", pady=(0, 25))

        sys_frame = ctk.CTkFrame(body, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12)
        sys_frame.pack(fill="x", pady=(0, 0))

        ctk.CTkLabel(sys_frame, text="Run at Windows Startup", font=font_label,
                     text_color=("#1A1A1A", "#FFFFFF"), anchor="w").pack(side="left", padx=20, pady=15)

        self.auto_start_var = ctk.BooleanVar(value=self.config_data["auto_start"])
        ctk.CTkSwitch(sys_frame, variable=self.auto_start_var,
                      button_color="#FFFFFF", button_hover_color="#E5E5EA",
                      progress_color=("#007AFF", "#0A84FF"),
                      fg_color=("#D1D1D6", "#39393D"),
                      width=50, height=30, corner_radius=15).pack(side="right", padx=20, pady=15)

        footer = ctk.CTkFrame(self.main_frame, fg_color="transparent", corner_radius=0)
        footer.pack(fill="x", padx=25, pady=(0, 25))

        ctk.CTkButton(footer, text="Save & Apply", font=font_btn,
                      height=50, corner_radius=14,
                      fg_color=("#007AFF", "#0A84FF"), hover_color=("#0062CC", "#1070FF"),
                      command=self.save_settings).pack(fill="x", side="bottom")

        self.bind_drag(self.main_frame)
        self.bind_drag(header)
        self.bind_drag(body)

    def bind_drag(self, widget):
        widget.bind("<ButtonPress-1>", self.start_move)
        widget.bind("<B1-Motion>", self.on_move)

    def start_listening_hotkey(self) -> None:
        self.hotkey_btn.configure(text="Press keys...")
        def capture():
            key = keyboard.read_hotkey()
            clean_key = sanitize_hotkey(key)
            self.new_hotkey = clean_key
            self.after(0, lambda: self.hotkey_btn.configure(text=clean_key))
        threading.Thread(target=capture, daemon=True).start()

    def change_theme(self, choice: str) -> None:
        ctk.set_appearance_mode(choice)

    def start_move(self, event) -> None:
        self.x = event.x
        self.y = event.y

    def on_move(self, event) -> None:
        x = self.winfo_x() + (event.x - self.x)
        y = self.winfo_y() + (event.y - self.y)
        self.geometry(f"+{x}+{y}")

    def animate_fade_in(self) -> None:
        if self.alpha < 0.95:
            self.alpha += 0.05
            self.wm_attributes("-alpha", str(self.alpha))
            self.after(10, self.animate_fade_in)
        else:
            self.wm_attributes("-alpha", "0.95")

    def animate_fade_out(self) -> None:
        if self.alpha > 0:
            self.alpha -= 0.05
            self.wm_attributes("-alpha", str(self.alpha))
            self.after(10, self.animate_fade_out)
        else:
            self.destroy()

    def save_settings(self) -> None:
        global CURRENT_HOTKEY
        old_hotkey = self.config_data["hotkey"]
        new_hotkey = self.new_hotkey

        if old_hotkey != new_hotkey and new_hotkey:
            try:
                keyboard.remove_hotkey(old_hotkey)
                keyboard.add_hotkey(new_hotkey, on_hotkey_press, suppress=True)
                self.config_data["hotkey"] = new_hotkey
                CURRENT_HOTKEY = new_hotkey
            except Exception:
                pass

        self.config_data["theme"] = self.theme_menu.get()
        self.config_data["auto_start"] = self.auto_start_var.get()
        save_config(self.config_data)

        if self.auto_start_var.get():
            add_to_startup()
        else:
            remove_from_startup()

        self.animate_fade_out()


# ==========================================
# 4. System Tray & Startup
# ==========================================
root = None
settings_window = None
tray_icon = None

def show_settings_window() -> None:
    global settings_window
    if settings_window is None or not settings_window.winfo_exists():
        config = load_config()
        settings_window = SettingsApp(root, config)
        settings_window.focus_force()

def open_settings(icon, item) -> None:
    if root:
        root.after(0, show_settings_window)

def quit_app(icon, item) -> None:
    global root, tray_icon
    if tray_icon:
        tray_icon.stop()
    if root:
        root.after(0, root.destroy)

def setup_tray() -> None:
    global tray_icon
    if os.path.exists(ICON_PATH):
        image = Image.open(ICON_PATH)
    else:
        from PIL import ImageDraw
        image = Image.new('RGB', (64, 64), (30, 30, 30))
        draw = ImageDraw.Draw(image)
        draw.rectangle([10, 20, 54, 44], fill=(0, 122, 255))

    menu = pystray.Menu(
        pystray.MenuItem("Settings", open_settings, default=True),
        pystray.MenuItem("Exit", quit_app)
    )
    tray_icon = pystray.Icon("keyboard_fixer", image, "Keyboard Fixer", menu)
    tray_icon.run()

def add_to_startup() -> None:
    try:
        # استفاده از مسیر واقعی فایل exe برای Nuitka
        if "__compiled__" in globals():
            app_path = f'"{os.path.abspath(sys.argv[0])}"'
        else:
            app_path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'

        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.SetValueEx(reg_key, "KeyboardFixer", 0, winreg.REG_SZ, app_path)
    except Exception:
        pass

def remove_from_startup() -> None:
    try:
        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.DeleteValue(reg_key, "KeyboardFixer")
    except FileNotFoundError:
        pass


# ==========================================
# 5. Main Entry Point
# ==========================================
if __name__ == "__main__":
    try:
        keyboard.unhook_all()
    except:
        pass

    config = load_config()
    ctk.set_appearance_mode(config["theme"])

    CURRENT_HOTKEY = config["hotkey"]

    if config["auto_start"]:
        add_to_startup()
    else:
        remove_from_startup()

    try:
        keyboard.add_hotkey(config["hotkey"], on_hotkey_press, suppress=True)
    except Exception:
        config["hotkey"] = "ctrl+alt+q"
        save_config(config)
        keyboard.add_hotkey(config["hotkey"], on_hotkey_press, suppress=True)
        CURRENT_HOTKEY = config["hotkey"]

    root = ctk.CTk()
    root.withdraw()

    if os.path.exists(ICON_PATH):
        root.iconbitmap(ICON_PATH)

    tray_thread = threading.Thread(target=setup_tray, daemon=True)
    tray_thread.start()

    try:
        root.mainloop()
    except KeyboardInterrupt:
        try:
            keyboard.unhook_all()
        except:
            pass
        if tray_icon:
            tray_icon.stop()
        sys.exit(0)
