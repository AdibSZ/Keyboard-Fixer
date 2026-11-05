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

    def get_executable_command(self) -> tuple[str, str]:
        """Returns (cmd_str, exe_path) suitable for autostart."""
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
            cmd = f'"{exe_path}" --silent'
            return cmd, exe_path

        # If running from source, check if compiled KeyboardFixer.exe exists in project folder
        script_dir = os.path.dirname(os.path.abspath(__file__))
        compiled_exe = os.path.join(script_dir, "KeyboardFixer.exe")
        if os.path.exists(compiled_exe):
            cmd = f'"{compiled_exe}" --silent'
            return cmd, compiled_exe

        # Fallback to pythonw.exe main.py
        python_exe = sys.executable
        pythonw_exe = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
        if not os.path.exists(pythonw_exe):
            pythonw_exe = python_exe
        script_path = os.path.join(script_dir, "main.py")
        cmd = f'"{pythonw_exe}" "{script_path}" --silent'
        return cmd, pythonw_exe

    def _create_startup_shortcut(self, exe_path: str):
        startup_dir = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
        if not os.path.isdir(startup_dir):
            return
        lnk_path = os.path.join(startup_dir, "KeyboardFixer.lnk")
        work_dir = os.path.dirname(os.path.abspath(exe_path))

        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(lnk_path)
            shortcut.TargetPath = exe_path
            shortcut.Arguments = "--silent"
            shortcut.WorkingDirectory = work_dir
            shortcut.Save()
            print(f"[Config] Startup shortcut created: {lnk_path}")
            return
        except Exception:
            pass

        try:
            ps_cmd = (
                f"$ws = New-Object -ComObject WScript.Shell; "
                f"$s = $ws.CreateShortcut('{lnk_path}'); "
                f"$s.TargetPath = '{exe_path}'; "
                f"$s.Arguments = '--silent'; "
                f"$s.WorkingDirectory = '{work_dir}'; "
                f"$s.Save()"
            )
            import subprocess
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                check=False
            )
            print(f"[Config] Startup shortcut created via PowerShell: {lnk_path}")
        except Exception as e:
            print(f"[Config] Failed to create startup shortcut: {e}")

    def _remove_startup_shortcut(self):
        startup_dir = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
        lnk_path = os.path.join(startup_dir, "KeyboardFixer.lnk")
        if os.path.exists(lnk_path):
            try:
                os.remove(lnk_path)
                print(f"[Config] Startup shortcut removed: {lnk_path}")
            except Exception:
                pass

    def sync_autostart_registry(self, enable: bool):
        """Registers or unregisters the app in Windows startup registry and Startup folder."""
        try:
            # 1. Update Windows Run Key
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REGISTRY_RUN_KEY,
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
            )

            if enable:
                cmd, exe_path = self.get_executable_command()
                winreg.SetValueEx(key, APP_REGISTRY_NAME, 0, winreg.REG_SZ, cmd)
                print(f"[Config] Autostart enabled in registry: {cmd}")
            else:
                try:
                    winreg.DeleteValue(key, APP_REGISTRY_NAME)
                    print("[Config] Autostart removed from registry.")
                except FileNotFoundError:
                    pass

            winreg.CloseKey(key)

            # 2. Windows StartupApproved Key (Ensure Windows / Task Manager doesn't block it)
            try:
                approved_key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run",
                    0,
                    winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
                )
                if enable:
                    # 0x02 = Enabled in Windows StartupApproved (12 bytes)
                    winreg.SetValueEx(
                        approved_key,
                        APP_REGISTRY_NAME,
                        0,
                        winreg.REG_BINARY,
                        b'\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                    )
                else:
                    winreg.SetValueEx(
                        approved_key,
                        APP_REGISTRY_NAME,
                        0,
                        winreg.REG_BINARY,
                        b'\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                    )
                winreg.CloseKey(approved_key)
            except Exception as e:
                print(f"[Config] StartupApproved registry sync note: {e}")

            # 3. Windows Startup Folder Shortcut (Guarantees autostart even if Run key is restricted)
            try:
                if enable:
                    _, exe_path = self.get_executable_command()
                    self._create_startup_shortcut(exe_path)
                else:
                    self._remove_startup_shortcut()
            except Exception as e:
                print(f"[Config] Startup folder shortcut sync note: {e}")

            self.set("start_with_windows", enable)
            return True
        except Exception as e:
            print(f"[Config] Error setting registry autostart: {e}")
            return False

    def is_autostart_in_registry(self) -> bool:
        """Checks if app is registered for autostart via registry or startup folder."""
        startup_dir = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
        lnk_path = os.path.join(startup_dir, "KeyboardFixer.lnk")
        if os.path.exists(lnk_path):
            return True

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_RUN_KEY, 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, APP_REGISTRY_NAME)
                winreg.CloseKey(key)

                # Check if it was disabled in StartupApproved
                try:
                    app_key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run",
                        0,
                        winreg.KEY_READ
                    )
                    val, _ = winreg.QueryValueEx(app_key, APP_REGISTRY_NAME)
                    winreg.CloseKey(app_key)
                    if isinstance(val, (bytes, bytearray)) and len(val) > 0:
                        if val[0] % 2 != 0:
                            return False
                except Exception:
                    pass

                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False
