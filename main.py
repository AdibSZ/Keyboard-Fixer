"""
Keyboard Fixer Pro - Main Application Entry Point
Authors: Antigravity & User
Description:
An elegant Windows utility that automatically fixes mistyped Persian/English text,
switches Windows keyboard layout seamlessly, provides custom mapping editing,
smart auto-word selection, floating OSD notifications, and integrates with System Tray and Startup.
"""
import os
import sys
import time
import threading
import ctypes
from ctypes import wintypes
import keyboard

# Configure UTF-8 encoding for stdout/stderr if available
if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config_manager import ConfigManager
from keyboard_engine import KeyboardEngine
from tray_manager import TrayManager
from ui_settings import SettingsWindow
from toast_notification import OSDToast

ERROR_ALREADY_EXISTS = 183
MUTEX_NAME = "KeyboardFixer_SingleInstance_Mutex_9918"

class KeyboardFixerApp:
    def __init__(self, show_ui_on_start=False):
        self.show_ui_on_start = show_ui_on_start
        self.is_active = True
        self.current_hotkey = ""

        # 1. Initialize Configuration
        self.config_mgr = ConfigManager()

        # 2. Initialize Engine
        self.engine = KeyboardEngine(
            preset=self.config_mgr.get("preset", "standard"),
            custom_normal=self.config_mgr.get("custom_normal", {}),
            custom_shifted=self.config_mgr.get("custom_shifted", {}),
            normalize_arabic=self.config_mgr.get("normalize_arabic", True)
        )

        # 3. Create Settings UI Window
        self.ui = SettingsWindow(
            config_manager=self.config_mgr,
            keyboard_engine=self.engine,
            on_hotkey_changed=self.update_hotkey,
            on_status_toggled=self.set_active_state
        )

        # 4. Initialize OSD Toast
        self.toast = OSDToast()

        # 5. Initialize System Tray
        self.tray = TrayManager(
            on_show_settings=self.show_settings_from_tray,
            on_toggle_active=self.set_active_state,
            on_convert_now=self.trigger_conversion,
            on_exit=self.exit_app
        )

        # 6. Register Global Hotkey
        initial_hotkey = self.config_mgr.get("hotkey", "ctrl+shift+f")
        self.update_hotkey(initial_hotkey)

    def trigger_conversion(self):
        """Called by hotkey or system tray 'Convert Now'."""
        if not self.is_active:
            return

        threading.Thread(target=self._run_conversion_worker, daemon=True).start()

    def _run_conversion_worker(self):
        result = self.engine.fix_selection(
            auto_switch=self.config_mgr.get("auto_switch_layout", True),
            sound_style=self.config_mgr.get("sound_style", "soft"),
            restore_clip=self.config_mgr.get("restore_clipboard", True),
            smart_word_select=self.config_mgr.get("smart_word_select", True)
        )

        if result.get("success"):
            orig = result.get("original", "")
            conv = result.get("converted", "")
            lang = result.get("target_lang", "fa")
            count = result.get("word_count", 1)

            # Update stats & history
            self.config_mgr.increment_words_fixed(count)
            self.config_mgr.add_history(orig, conv, lang)

            # Update UI stats if window exists
            self.ui.after(0, self.ui.update_stats_display)

            # Show floating toast notification if enabled
            if self.config_mgr.get("show_toast", True):
                self.ui.after(0, lambda: self.toast.show(orig, conv, lang))

    def update_hotkey(self, new_hotkey_str: str) -> bool:
        """Dynamically registers or updates the global shortcut safely."""
        try:
            # Ensure keyboard listener is initialized
            keyboard._listener.start_if_necessary()
            try:
                keyboard.unhook_all_hotkeys()
            except Exception:
                pass

            # Register new hotkey (suppress=False prevents keyboard hook deadlocks)
            keyboard.add_hotkey(new_hotkey_str, self.trigger_conversion, suppress=False)
            self.current_hotkey = new_hotkey_str
            print(f"[App] Global shortcut registered: {new_hotkey_str}")
            return True
        except Exception as e:
            print(f"[App] Failed to bind shortcut '{new_hotkey_str}': {e}")
            return False

    def set_active_state(self, active: bool):
        """Pauses or resumes service."""
        self.is_active = active
        self.tray.set_active_state(active)
        if hasattr(self.ui, "service_switch"):
            if active and self.ui.service_switch.get() == 0:
                self.ui.service_switch.select()
            elif not active and self.ui.service_switch.get() == 1:
                self.ui.service_switch.deselect()

            if active:
                self.ui.status_badge.configure(text="● Active", text_color="#10b981", fg_color="#064e3b")
            else:
                self.ui.status_badge.configure(text="⏸ Paused", text_color="#f59e0b", fg_color="#451a03")

    def show_settings_from_tray(self):
        """Brings the UI window to front from the system tray thread."""
        self.ui.after(0, self.ui.show_window)

    def exit_app(self):
        """Completely cleans up and exits."""
        print("[App] Exiting Keyboard Fixer...")
        try:
            keyboard._listener.start_if_necessary()
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        self.tray.stop()
        self.ui.after(0, self._destroy_ui_and_quit)

    def _destroy_ui_and_quit(self):
        try:
            self.ui.destroy()
        except Exception:
            pass
        sys.exit(0)

    def run(self):
        """Starts tray and enters Tkinter mainloop."""
        self.tray.start()

        if self.show_ui_on_start:
            self.ui.show_window()
        else:
            self.ui.hide_to_tray()

        self.ui.mainloop()


def ensure_single_instance():
    """Uses a Windows Mutex to ensure only one instance of Keyboard Fixer runs."""
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    last_error = ctypes.windll.kernel32.GetLastError()
    if last_error == ERROR_ALREADY_EXISTS:
        return None
    return mutex


def main():
    mutex = ensure_single_instance()
    if not mutex:
        print("[App] Keyboard Fixer is already running in background/tray.")
        try:
            ctypes.windll.user32.MessageBoxW(
                0,
                "Keyboard Fixer is already running in the background (System Tray near clock).\nClick the tray icon to open Settings.",
                "Keyboard Fixer Pro",
                0x00000040  # MB_ICONINFORMATION
            )
        except Exception:
            pass
        sys.exit(0)

    show_ui = True if ("--settings" in sys.argv or "--show" in sys.argv) else False
    
    if not os.path.exists("config.json"):
        show_ui = True

    app = KeyboardFixerApp(show_ui_on_start=show_ui)
    app.run()


if __name__ == "__main__":
    main()
