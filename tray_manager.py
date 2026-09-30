"""
System tray manager for Keyboard Fixer.
Handles the system tray icon, context menu, and background lifecycle using pystray.
"""
import os
import sys
import threading
from PIL import Image
import pystray
from pystray import MenuItem as item

BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
ICON_PATH = os.path.join(BASE_DIR, "assets", "icon.png")

class TrayManager:
    def __init__(self, on_show_settings, on_toggle_active, on_convert_now, on_exit):
        self.on_show_settings = on_show_settings
        self.on_toggle_active = on_toggle_active
        self.on_convert_now = on_convert_now
        self.on_exit = on_exit
        self.icon = None
        self.is_active = True
        self.tray_thread = None

    def _get_icon_image(self):
        if os.path.exists(ICON_PATH):
            try:
                return Image.open(ICON_PATH)
            except Exception:
                pass
        img = Image.new("RGBA", (64, 64), (37, 99, 235, 255))
        return img

    def _build_menu(self):
        return pystray.Menu(
            item("Keyboard Fixer Pro", lambda: None, enabled=False),
            item(
                lambda text: "✅ Service Active" if self.is_active else "⏸ Service Paused",
                self._handle_toggle_active,
                checked=lambda item: self.is_active
            ),
            pystray.Menu.SEPARATOR,
            item("⚙️ Settings", self._handle_show_settings, default=True),
            item("🔄 Convert Selection", self._handle_convert_now),
            pystray.Menu.SEPARATOR,
            item("❌ Exit", self._handle_exit)
        )

    def _handle_show_settings(self, icon=None, item=None):
        if self.on_show_settings:
            self.on_show_settings()

    def _handle_toggle_active(self, icon=None, item=None):
        self.is_active = not self.is_active
        if self.on_toggle_active:
            self.on_toggle_active(self.is_active)
        if self.icon:
            self.icon.update_menu()

    def _handle_convert_now(self, icon=None, item=None):
        if self.on_convert_now:
            self.on_convert_now()

    def _handle_exit(self, icon=None, item=None):
        self.stop()
        if self.on_exit:
            self.on_exit()

    def start(self):
        image = self._get_icon_image()
        self.icon = pystray.Icon(
            name="KeyboardFixer",
            icon=image,
            title="Keyboard Fixer Pro",
            menu=self._build_menu()
        )
        self.tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        self.tray_thread.start()
        print("[Tray] System tray icon started.")

    def set_active_state(self, active: bool):
        self.is_active = active
        if self.icon:
            self.icon.update_menu()

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None
            print("[Tray] System tray icon stopped.")
