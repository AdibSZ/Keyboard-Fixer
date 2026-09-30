"""
Modern, Minimalist & Sleek UI for Keyboard Fixer Pro.
Design Philosophy:
- Luxury Obsidian Dark Theme (#090d16)
- Crisp Windows 11 Typography (Segoe UI Variable)
- Clean, uncluttered layout: Hero Dashboard + Key Mappings Viewer
- Instant Live Test bar
- High-DPI crystal clear rendering
"""
import os
import sys
import ctypes
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image

# Enable Windows High-DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from keyboard_engine import (
    KEY_LABELS_EN, SHIFT_LABELS_EN, STANDARD_NORMAL, STANDARD_SHIFTED,
    LEGACY_NORMAL, LEGACY_SHIFTED
)

# Global appearance settings
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ICON_ICO = os.path.join(ASSETS_DIR, "icon.ico")
ICON_PNG = os.path.join(ASSETS_DIR, "icon.png")

# Best available modern fonts on Windows 10/11
TITLE_FONT = ("Segoe UI Variable Display", 20, "bold")
SUBTITLE_FONT = ("Segoe UI Variable Text", 12)
CARD_TITLE_FONT = ("Segoe UI Variable Display", 14, "bold")
BODY_FONT = ("Segoe UI Variable Text", 13)
CAPTION_FONT = ("Segoe UI Variable Text", 11)
BADGE_FONT = ("Segoe UI Variable Display", 11, "bold")
CODE_FONT = ("Consolas", 13, "bold")

# Luxury Color Palette
BG_COLOR = "#090d16"           # Ultra-dark slate
CARD_BG = "#111827"            # Card background
CARD_BORDER = "#1f2937"        # Subtle card border
ACCENT_BLUE = "#3b82f6"        # Electric Blue
ACCENT_EMERALD = "#10b981"     # Emerald Green
TEXT_PRIMARY = "#f9fafb"       # Bright White
TEXT_SECONDARY = "#9ca3af"     # Muted Slate

class SettingsWindow(ctk.CTk):
    def __init__(self, config_manager, keyboard_engine, on_hotkey_changed=None, on_status_toggled=None):
        super().__init__()

        self.cfg = config_manager
        self.engine = keyboard_engine
        self.on_hotkey_changed = on_hotkey_changed
        self.on_status_toggled = on_status_toggled
        self.is_service_active = True
        self.is_recording_hotkey = False
        self.recorded_keys = set()

        # Window Setup
        self.title("Keyboard Fixer")
        self.geometry("580x640")
        self.minsize(540, 580)
        self.configure(fg_color=BG_COLOR)

        if os.path.exists(ICON_ICO):
            try:
                self.iconbitmap(ICON_ICO)
            except Exception:
                pass

        # Close button minimizes to tray
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self.mapping_entries = {}
        self.current_editor_mode = "normal"
        self.mappings_window = None

        # Build UI
        self._build_ui()
        self._load_settings_values()

    def _build_ui(self):
        # 1. Header Frame
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 12))

        # Logo & App Title
        left_box = ctk.CTkFrame(header, fg_color="transparent")
        left_box.pack(side="left")

        if os.path.exists(ICON_PNG):
            try:
                pil_img = Image.open(ICON_PNG)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(38, 38))
                icon_lbl = ctk.CTkLabel(left_box, image=ctk_img, text="")
                icon_lbl.pack(side="left", padx=(0, 12))
            except Exception:
                pass

        title_text_box = ctk.CTkFrame(left_box, fg_color="transparent")
        title_text_box.pack(side="left")

        title_lbl = ctk.CTkLabel(
            title_text_box,
            text="Keyboard Fixer",
            font=ctk.CTkFont(family=TITLE_FONT[0], size=TITLE_FONT[1], weight=TITLE_FONT[2]),
            text_color=TEXT_PRIMARY
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = ctk.CTkLabel(
            title_text_box,
            text="Smart typo fixer for Persian & English",
            font=ctk.CTkFont(family=SUBTITLE_FONT[0], size=SUBTITLE_FONT[1]),
            text_color=TEXT_SECONDARY
        )
        subtitle_lbl.pack(anchor="w")

        # Master Service Toggle
        self.service_switch = ctk.CTkSwitch(
            header,
            text="Active",
            font=ctk.CTkFont(family=BADGE_FONT[0], size=13, weight="bold"),
            progress_color=ACCENT_EMERALD,
            command=self._on_service_toggle
        )
        self.service_switch.pack(side="right", pady=4)

        # 2. Hero Shortcut Card
        shortcut_card = ctk.CTkFrame(
            self,
            fg_color=CARD_BG,
            corner_radius=14,
            border_width=1,
            border_color=CARD_BORDER
        )
        shortcut_card.pack(fill="x", padx=24, pady=(0, 14))

        sc_top = ctk.CTkFrame(shortcut_card, fg_color="transparent")
        sc_top.pack(fill="x", padx=18, pady=(14, 8))

        sc_title = ctk.CTkLabel(
            sc_top,
            text="Trigger Shortcut",
            font=ctk.CTkFont(family=CARD_TITLE_FONT[0], size=CARD_TITLE_FONT[1], weight=CARD_TITLE_FONT[2]),
            text_color=TEXT_PRIMARY
        )
        sc_title.pack(side="left")

        self.words_stat_badge = ctk.CTkLabel(
            sc_top,
            text=f"⚡ {self.cfg.get('stats_words_fixed', 0)} Fixed",
            font=ctk.CTkFont(family=BADGE_FONT[0], size=11, weight="bold"),
            text_color=ACCENT_BLUE,
            fg_color="#1e3a8a",
            corner_radius=6,
            padx=10,
            pady=2
        )
        self.words_stat_badge.pack(side="right")

        # Active Shortcut Display Row
        sc_action_row = ctk.CTkFrame(shortcut_card, fg_color="transparent")
        sc_action_row.pack(fill="x", padx=18, pady=(0, 10))

        self.hotkey_badge = ctk.CTkLabel(
            sc_action_row,
            text="Ctrl + Shift + F",
            font=ctk.CTkFont(family=CODE_FONT[0], size=15, weight="bold"),
            fg_color="#1f2937",
            text_color="#60a5fa",
            corner_radius=8,
            padx=16,
            pady=8
        )
        self.hotkey_badge.pack(side="left")

        self.record_btn = ctk.CTkButton(
            sc_action_row,
            text="🎤 Record Key",
            font=ctk.CTkFont(family=BODY_FONT[0], size=12, weight="bold"),
            width=110,
            height=34,
            fg_color=ACCENT_BLUE,
            hover_color="#2563eb",
            command=self._start_recording_hotkey
        )
        self.record_btn.pack(side="right", padx=(8, 0))

        # Quick Presets Row
        presets_row = ctk.CTkFrame(shortcut_card, fg_color="transparent")
        presets_row.pack(fill="x", padx=18, pady=(0, 14))

        quick_lbl = ctk.CTkLabel(
            presets_row,
            text="Presets:",
            font=ctk.CTkFont(family=CAPTION_FONT[0], size=11),
            text_color=TEXT_SECONDARY
        )
        quick_lbl.pack(side="left", padx=(0, 6))

        for sc in ["ctrl+shift+f", "f9", "pause", "ctrl+space"]:
            disp = sc.upper().replace("+", " + ")
            b = ctk.CTkButton(
                presets_row,
                text=disp,
                width=75,
                height=24,
                font=ctk.CTkFont(family=CODE_FONT[0], size=10),
                fg_color="#1f2937",
                hover_color="#374151",
                text_color="#d1d5db",
                command=lambda s=sc: self._set_quick_hotkey(s)
            )
            b.pack(side="left", padx=3)

        # 3. Preferences Card (Modern Minimalist Toggles)
        pref_card = ctk.CTkFrame(
            self,
            fg_color=CARD_BG,
            corner_radius=14,
            border_width=1,
            border_color=CARD_BORDER
        )
        pref_card.pack(fill="x", padx=24, pady=(0, 14))

        # Toggle 1: Auto-fix last word
        self.smart_word_var = ctk.BooleanVar(value=True)
        t1_box = ctk.CTkFrame(pref_card, fg_color="transparent")
        t1_box.pack(fill="x", padx=18, pady=(12, 6))
        
        t1_text = ctk.CTkFrame(t1_box, fg_color="transparent")
        t1_text.pack(side="left")
        ctk.CTkLabel(t1_text, text="⚡ Auto-Fix Last Word", font=ctk.CTkFont(family=BODY_FONT[0], size=13, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(t1_text, text="Fix the word you just typed without selecting it", font=ctk.CTkFont(family=CAPTION_FONT[0], size=11), text_color=TEXT_SECONDARY).pack(anchor="w")

        ctk.CTkSwitch(t1_box, text="", variable=self.smart_word_var, progress_color=ACCENT_BLUE, width=42, command=self._on_smart_word_change).pack(side="right")

        # Divider
        ctk.CTkFrame(pref_card, fg_color=CARD_BORDER, height=1).pack(fill="x", padx=18, pady=4)

        # Toggle 2: Auto switch keyboard language
        self.switch_layout_var = ctk.BooleanVar(value=True)
        t2_box = ctk.CTkFrame(pref_card, fg_color="transparent")
        t2_box.pack(fill="x", padx=18, pady=6)

        t2_text = ctk.CTkFrame(t2_box, fg_color="transparent")
        t2_text.pack(side="left")
        ctk.CTkLabel(t2_text, text="🌐 Switch Keyboard Language", font=ctk.CTkFont(family=BODY_FONT[0], size=13, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(t2_text, text="Automatically switch Windows layout to FA / EN", font=ctk.CTkFont(family=CAPTION_FONT[0], size=11), text_color=TEXT_SECONDARY).pack(anchor="w")

        ctk.CTkSwitch(t2_box, text="", variable=self.switch_layout_var, progress_color=ACCENT_BLUE, width=42, command=self._on_switch_layout_change).pack(side="right")

        # Divider
        ctk.CTkFrame(pref_card, fg_color=CARD_BORDER, height=1).pack(fill="x", padx=18, pady=4)

        # Toggle 3: Floating OSD
        self.toast_var = ctk.BooleanVar(value=True)
        t3_box = ctk.CTkFrame(pref_card, fg_color="transparent")
        t3_box.pack(fill="x", padx=18, pady=6)

        t3_text = ctk.CTkFrame(t3_box, fg_color="transparent")
        t3_text.pack(side="left")
        ctk.CTkLabel(t3_text, text="💬 On-Screen Notification", font=ctk.CTkFont(family=BODY_FONT[0], size=13, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(t3_text, text="Show sleek floating pill when text is fixed", font=ctk.CTkFont(family=CAPTION_FONT[0], size=11), text_color=TEXT_SECONDARY).pack(anchor="w")

        ctk.CTkSwitch(t3_box, text="", variable=self.toast_var, progress_color=ACCENT_BLUE, width=42, command=self._on_toast_change).pack(side="right")

        # Divider
        ctk.CTkFrame(pref_card, fg_color=CARD_BORDER, height=1).pack(fill="x", padx=18, pady=4)

        # Toggle 4: Start on boot & Sound style row
        t4_box = ctk.CTkFrame(pref_card, fg_color="transparent")
        t4_box.pack(fill="x", padx=18, pady=(6, 12))

        # Sound dropdown
        sound_box = ctk.CTkFrame(t4_box, fg_color="transparent")
        sound_box.pack(side="left")
        ctk.CTkLabel(sound_box, text="🔊 Sound Feedback:", font=ctk.CTkFont(family=BODY_FONT[0], size=12), text_color=TEXT_SECONDARY).pack(side="left", padx=(0, 6))
        self.sound_combo = ctk.CTkOptionMenu(
            sound_box,
            values=["Soft Click", "Chime", "System Beep", "Mute"],
            width=115,
            height=28,
            font=ctk.CTkFont(family=BODY_FONT[0], size=11),
            fg_color="#1f2937",
            button_color="#374151",
            command=self._on_sound_style_change
        )
        self.sound_combo.pack(side="left")

        # Start with windows switch
        self.autostart_var = ctk.BooleanVar(value=False)
        start_box = ctk.CTkFrame(t4_box, fg_color="transparent")
        start_box.pack(side="right")
        ctk.CTkLabel(start_box, text="Start on Boot", font=ctk.CTkFont(family=BODY_FONT[0], size=12), text_color=TEXT_SECONDARY).pack(side="left", padx=(0, 6))
        ctk.CTkSwitch(start_box, text="", variable=self.autostart_var, progress_color=ACCENT_BLUE, width=40, command=self._on_autostart_change).pack(side="left")

        # 4. Live Test Card (Interactive & Instant)
        test_card = ctk.CTkFrame(
            self,
            fg_color=CARD_BG,
            corner_radius=14,
            border_width=1,
            border_color=CARD_BORDER
        )
        test_card.pack(fill="x", padx=24, pady=(0, 14))

        test_row = ctk.CTkFrame(test_card, fg_color="transparent")
        test_row.pack(fill="x", padx=16, pady=12)

        self.test_entry = ctk.CTkEntry(
            test_row,
            placeholder_text="Try typing here: sghl, Cghl, or آزمایش...",
            font=ctk.CTkFont(family=BODY_FONT[0], size=13),
            height=36,
            fg_color="#1f2937",
            border_color=CARD_BORDER
        )
        self.test_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.test_entry.bind("<KeyRelease>", lambda e: self._on_live_test_input())

        self.test_result_badge = ctk.CTkLabel(
            test_row,
            text="Result: Ready",
            font=ctk.CTkFont(family=BODY_FONT[0], size=12, weight="bold"),
            text_color=ACCENT_EMERALD,
            width=130
        )
        self.test_result_badge.pack(side="right")

        # 5. Bottom Navigation / Modal Buttons
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=24, pady=(0, 18))

        mapping_btn = ctk.CTkButton(
            footer,
            text="⌨️ Key Mappings",
            font=ctk.CTkFont(family=BODY_FONT[0], size=12),
            fg_color="#1f2937",
            hover_color="#374151",
            text_color=TEXT_PRIMARY,
            height=32,
            command=self._open_mappings_modal
        )
        mapping_btn.pack(side="left", padx=(0, 8))

        hide_btn = ctk.CTkButton(
            footer,
            text="⬇️ Minimize to Tray",
            font=ctk.CTkFont(family=BODY_FONT[0], size=12),
            fg_color="#1f2937",
            hover_color="#374151",
            text_color=TEXT_SECONDARY,
            height=32,
            command=self.hide_to_tray
        )
        hide_btn.pack(side="right")

    # ==========================================
    # LIVE TEST HANDLER
    # ==========================================
    def _on_live_test_input(self):
        text = self.test_entry.get().strip()
        if not text:
            self.test_result_badge.configure(text="Result: Ready", text_color=TEXT_SECONDARY)
            return

        converted, lang = self.engine.convert_text(text)
        badge_text = f"➔ {converted}"
        if len(badge_text) > 18:
            badge_text = badge_text[:16] + "…"
        self.test_result_badge.configure(text=badge_text, text_color=ACCENT_EMERALD)

    # ==========================================
    # MAPPINGS MODAL (CLEAN & MINIMALIST)
    # ==========================================
    def _open_mappings_modal(self):
        if self.mappings_window and self.mappings_window.winfo_exists():
            self.mappings_window.lift()
            self.mappings_window.focus_force()
            return

        self.mappings_window = ctk.CTkToplevel(self)
        self.mappings_window.title("Key Mappings - Keyboard Fixer")
        self.mappings_window.geometry("520x560")
        self.mappings_window.minsize(480, 480)
        self.mappings_window.configure(fg_color=BG_COLOR)

        top_bar = ctk.CTkFrame(self.mappings_window, fg_color="transparent")
        top_bar.pack(fill="x", padx=16, pady=12)

        preset_combo = ctk.CTkOptionMenu(
            top_bar,
            values=["Persian Standard (ISIRI 9147)", "Windows Legacy"],
            font=ctk.CTkFont(family=BODY_FONT[0], size=12),
            fg_color="#1f2937",
            button_color="#374151",
            command=self._on_preset_change_modal
        )
        preset_combo.pack(side="left")

        mode_seg = ctk.CTkSegmentedButton(
            top_bar,
            values=["Normal Keys", "Shifted Keys (ژ, ZWNJ, etc.)"],
            font=ctk.CTkFont(family=BODY_FONT[0], size=11),
            command=self._on_modal_mode_switched
        )
        mode_seg.set("Normal Keys")
        mode_seg.pack(side="right")

        # Scrollable area
        self.modal_scroll = ctk.CTkScrollableFrame(
            self.mappings_window,
            fg_color=CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=CARD_BORDER
        )
        self.modal_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        self._render_modal_mappings("normal")

    def _render_modal_mappings(self, mode):
        for w in self.modal_scroll.winfo_children():
            w.destroy()

        is_shifted = (mode == "shifted")
        active_map = self.engine.active_shifted if is_shifted else self.engine.active_normal
        labels_map = SHIFT_LABELS_EN if is_shifted else KEY_LABELS_EN

        for en_key, fa_char in active_map.items():
            row = ctk.CTkFrame(self.modal_scroll, fg_color="#1f2937", corner_radius=6, height=36)
            row.pack(fill="x", padx=6, pady=2)

            key_lbl = ctk.CTkLabel(
                row,
                text=f"Shift + {en_key}" if is_shifted and len(en_key) == 1 and en_key.isupper() else en_key,
                font=ctk.CTkFont(family=CODE_FONT[0], size=12, weight="bold"),
                width=110,
                text_color="#60a5fa"
            )
            key_lbl.pack(side="left", padx=8, pady=4)

            arrow = ctk.CTkLabel(row, text="➔", font=ctk.CTkFont(family=BODY_FONT[0], size=12), text_color=TEXT_SECONDARY)
            arrow.pack(side="left", padx=4)

            display_char = "ZWNJ (نیم‌فاصله)" if fa_char == "\u200c" else fa_char
            val_lbl = ctk.CTkLabel(
                row,
                text=display_char,
                font=ctk.CTkFont(family=BODY_FONT[0], size=13, weight="bold"),
                text_color=ACCENT_EMERALD,
                width=90
            )
            val_lbl.pack(side="left", padx=8)

            desc = labels_map.get(en_key, "")
            desc_lbl = ctk.CTkLabel(row, text=desc, font=ctk.CTkFont(family=CAPTION_FONT[0], size=10), text_color=TEXT_SECONDARY)
            desc_lbl.pack(side="left", padx=8)

    def _on_modal_mode_switched(self, choice):
        mode = "shifted" if "Shift" in choice else "normal"
        self._render_modal_mappings(mode)

    def _on_preset_change_modal(self, choice):
        if "Standard" in choice:
            self.cfg.set("preset", "standard")
            self.engine.preset = "standard"
        else:
            self.cfg.set("preset", "legacy")
            self.engine.preset = "legacy"
        self.engine.rebuild_maps()
        self._render_modal_mappings("normal")

    # ==========================================
    # INTERACTIVE HOTKEY RECORDER
    # ==========================================
    def _start_recording_hotkey(self):
        if self.is_recording_hotkey:
            return

        self.is_recording_hotkey = True
        self.recorded_keys.clear()
        self.record_btn.configure(
            text="Press Keys...",
            fg_color="#f59e0b",
            hover_color="#d97706"
        )
        self.hotkey_badge.configure(text="Recording...", text_color="#f59e0b")
        self.bind("<KeyPress>", self._on_key_record_press)

    def _on_key_record_press(self, event):
        if not self.is_recording_hotkey:
            return

        key_name = event.keysym.lower()

        if "control" in key_name:
            self.recorded_keys.add("ctrl")
        elif "shift" in key_name:
            self.recorded_keys.add("shift")
        elif "alt" in key_name:
            self.recorded_keys.add("alt")
        elif key_name == "space":
            self.recorded_keys.add("space")
        elif key_name in ["escape", "return"]:
            self._stop_recording_hotkey()
            return
        else:
            self.recorded_keys.add(key_name)
            self._finalize_recorded_hotkey()

    def _finalize_recorded_hotkey(self):
        ordered = []
        for mod in ["ctrl", "alt", "shift"]:
            if mod in self.recorded_keys:
                ordered.append(mod)
        for k in self.recorded_keys:
            if k not in ["ctrl", "alt", "shift"]:
                ordered.append(k)

        combo_str = "+".join(ordered)
        self._stop_recording_hotkey()
        self._set_quick_hotkey(combo_str)

    def _stop_recording_hotkey(self):
        self.is_recording_hotkey = False
        self.unbind("<KeyPress>")
        self.record_btn.configure(
            text="🎤 Record Key",
            fg_color=ACCENT_BLUE,
            hover_color="#2563eb"
        )

    # ==========================================
    # SETTINGS LOGIC & EVENT HANDLERS
    # ==========================================
    def update_stats_display(self):
        cnt = self.cfg.get("stats_words_fixed", 0)
        self.words_stat_badge.configure(text=f"⚡ {cnt} Fixed")

    def _load_settings_values(self):
        hk = self.cfg.get("hotkey", "ctrl+shift+f")
        self.hotkey_badge.configure(text=hk.upper().replace("+", " + "))

        self.smart_word_var.set(self.cfg.get("smart_word_select", True))
        self.toast_var.set(self.cfg.get("show_toast", True))
        self.switch_layout_var.set(self.cfg.get("auto_switch_layout", True))
        self.autostart_var.set(self.cfg.is_autostart_in_registry())

        s_style = self.cfg.get("sound_style", "soft")
        sound_map = {
            "soft": "Soft Click",
            "chime": "Chime",
            "beep": "System Beep",
            "none": "Mute"
        }
        self.sound_combo.set(sound_map.get(s_style, "Soft Click"))
        self.service_switch.select()

    def _set_quick_hotkey(self, shortcut):
        shortcut = shortcut.strip().lower()
        if not shortcut:
            return

        self.cfg.set("hotkey", shortcut)
        self.hotkey_badge.configure(text=shortcut.upper().replace("+", " + "), text_color="#60a5fa")

        if self.on_hotkey_changed:
            self.on_hotkey_changed(shortcut)

    def _on_service_toggle(self):
        active = self.service_switch.get() == 1
        self.is_service_active = active
        self.service_switch.configure(text="Active" if active else "Paused")
        if self.on_status_toggled:
            self.on_status_toggled(active)

    def _on_smart_word_change(self):
        self.cfg.set("smart_word_select", self.smart_word_var.get())

    def _on_toast_change(self):
        self.cfg.set("show_toast", self.toast_var.get())

    def _on_switch_layout_change(self):
        self.cfg.set("auto_switch_layout", self.switch_layout_var.get())

    def _on_autostart_change(self):
        val = self.autostart_var.get()
        self.cfg.sync_autostart_registry(val)

    def _on_sound_style_change(self, choice):
        style = "soft"
        if "Chime" in choice:
            style = "chime"
        elif "Beep" in choice:
            style = "beep"
        elif "Mute" in choice:
            style = "none"

        self.cfg.set("sound_style", style)
        self.engine.play_sound(style)

    def show_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def hide_to_tray(self):
        self.withdraw()
