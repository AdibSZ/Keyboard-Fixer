"""
Configuration manager for Keyboard Fixer.
Handles loading/saving settings, statistics, history, and Windows startup registry integration.
"""
import os
import sys
import json
import time
import winreg

def get_config_path() -> str:
    """Returns the persistent config file path in %APPDATA%\\KeyboardFixer."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        config_dir = os.path.join(appdata, "KeyboardFixer")
    else:
        config_dir = os.path.join(os.path.expanduser("~"), ".keyboard_fixer")
    
    os.makedirs(config_dir, exist_ok=True)
    target = os.path.join(config_dir, "config.json")

    # If the AppData config doesn't exist yet, migrate from local directory if present
    if not os.path.exists(target):
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"),
            os.path.join(os.path.dirname(sys.executable), "config.json")
        ]
        for c in candidates:
            if os.path.exists(c) and os.path.abspath(c) != os.path.abspath(target):
                try:
                    import shutil
                    shutil.copy2(c, target)
                    break
                except Exception:
                    pass
    return target

CONFIG_FILE = get_config_path()
REGISTRY_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_REGISTRY_NAME = "KeyboardFixer"

DEFAULT_CONFIG = {
    "hotkey": "ctrl+shift+f",
    "auto_switch_layout": True,
    "sound_style": "soft",             # "soft" | "chime" | "beep" | "none"
    "smart_word_select": True,         # auto-select last word if no text selected
    "show_toast": True,                # floating OSD notification
    "normalize_arabic": True,          # convert Arabic ي / ك to Persian ی / ک
    "restore_clipboard": True,
    "start_with_windows": False,
    "preset": "standard",              # "standard" | "legacy" | "custom"
    "custom_normal": {},
    "custom_shifted": {},
    "stats_words_fixed": 0,
    "history": []                      # List of recent conversions (max 25)
}

class ConfigManager:
    def __init__(self, config_path=CONFIG_FILE):
        self.config_path = config_path
        self.config = DEFAULT_CONFIG.copy()
        self.load()
        if self.config.get("start_with_windows", False):
            try:
                self.sync_autostart_registry(True)
            except Exception:
                pass

    def load(self):
        """Loads configuration from disk, creating default if missing."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config = {**DEFAULT_CONFIG, **data}
            except Exception as e:
                print(f"[Config] Error reading {self.config_path}: {e}")
                self.config = DEFAULT_CONFIG.copy()
        else:
            self.save()

    def save(self):
        """Saves current configuration to disk."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[Config] Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def increment_words_fixed(self, count=1):
        """Updates words converted statistic counter."""
        self.config["stats_words_fixed"] = self.config.get("stats_words_fixed", 0) + count
        self.save()

    def add_history(self, orig: str, conv: str, lang: str):
        """Adds a conversion entry to history (keeps last 25)."""
        if "history" not in self.config:
            self.config["history"] = []

        entry = {
            "time": time.strftime("%H:%M:%S"),
            "orig": orig[:60],
            "conv": conv[:60],
            "lang": lang
        }
        self.config["history"].insert(0, entry)
        if len(self.config["history"]) > 25:
            self.config["history"] = self.config["history"][:25]
        self.save()

    def clear_history(self):
        self.config["history"] = []
        self.save()

    def update_custom_key(self, key_type: str, char_en: str, char_fa: str):
        """Updates a single custom key mapping."""
        dict_key = "custom_normal" if key_type == "normal" else "custom_shifted"
        if dict_key not in self.config:
            self.config[dict_key] = {}
        
        self.config[dict_key][char_en] = char_fa
        self.config["preset"] = "custom"
        self.save()

    def reset_mappings(self, preset="standard"):
        """Resets custom key mappings to the specified preset."""
        self.config["custom_normal"] = {}
        self.config["custom_shifted"] = {}
        self.config["preset"] = preset
        self.save()

    def sync_autostart_registry(self, enable: bool):
        """Registers or unregisters the app in Windows startup registry."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REGISTRY_RUN_KEY,
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
            )

            if enable:
                if getattr(sys, 'frozen', False):
                    cmd = f'"{sys.executable}" --silent'
                else:
                    python_exe = sys.executable
                    pythonw_exe = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
                    if not os.path.exists(pythonw_exe):
                        pythonw_exe = python_exe
                    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
                    cmd = f'"{pythonw_exe}" "{script_path}" --silent'

                winreg.SetValueEx(key, APP_REGISTRY_NAME, 0, winreg.REG_SZ, cmd)
                print(f"[Config] Autostart enabled in registry: {cmd}")
            else:
                try:
                    winreg.DeleteValue(key, APP_REGISTRY_NAME)
                    print("[Config] Autostart removed from registry.")
                except FileNotFoundError:
                    pass

            winreg.CloseKey(key)
            self.set("start_with_windows", enable)
            return True
        except Exception as e:
            print(f"[Config] Error setting registry autostart: {e}")
            return False

    def is_autostart_in_registry(self) -> bool:
        """Checks if app is currently registered in Windows Run registry."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_RUN_KEY, 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, APP_REGISTRY_NAME)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False
