"""
Keyboard Fixer Engine.
Handles layout definitions, bidirectional conversion, Win32 layout switching,
and bidirectional RTL/LTR aware smart word auto-selection.
"""
import ctypes
from ctypes import wintypes
import time
import winsound
import pyperclip

# Win32 Constants
WM_INPUTLANGCHANGEREQUEST = 0x0050
KLF_ACTIVATE = 0x00000001
KLF_SETFORPROCESS = 0x00000100

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001

VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12    # Alt
VK_SPACE = 0x20
VK_LEFT = 0x25
VK_RIGHT = 0x27
VK_C = 0x43
VK_V = 0x56

user32 = ctypes.windll.user32

# ==========================================
# PRESET DEFINITIONS
# ==========================================

STANDARD_NORMAL = {
    '`': '\u200c', '1': '۱', '2': '۲', '3': '۳', '4': '۴', '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹', '0': '۰', '-': '-', '=': '=',
    'q': 'ض', 'w': 'ص', 'e': 'ث', 'r': 'ق', 't': 'ف', 'y': 'غ', 'u': 'ع', 'i': 'ه', 'o': 'خ', 'p': 'ح', '[': 'ج', ']': 'چ', '\\': 'پ',
    'a': 'ش', 's': 'س', 'd': 'ی', 'f': 'ب', 'g': 'ل', 'h': 'ا', 'j': 'ت', 'k': 'ن', 'l': 'م', ';': 'ک', "'": 'گ',
    'z': 'ظ', 'x': 'ط', 'c': 'ز', 'v': 'ر', 'b': 'ذ', 'n': 'د', 'm': 'ئ', ',': 'و', '.': '.', '/': '/'
}

STANDARD_SHIFTED = {
    '~': '÷', '!': '!', '@': '٬', '#': '٫', '$': '﷼', '%': '٪', '^': '×', '&': '،', '*': '*', '(': ')', ')': '(', '_': '_', '+': '+',
    'Q': 'ً', 'W': 'ٌ', 'E': 'ٍ', 'R': 'ْ', 'T': '،', 'Y': '؛', 'U': ',', 'I': ']', 'O': '[', 'P': '\\', '{': '}', '}': '{', '|': '|',
    'A': 'َ', 'S': 'ُ', 'D': 'ِ', 'F': 'ّ', 'G': 'ۀ', 'H': 'آ', 'J': 'ـ', 'K': '«', 'L': '»', ':': ':', '"': '"',
    'Z': 'ك', 'X': 'ٓ', 'C': 'ژ', 'V': '\u200c', 'B': 'إ', 'N': 'أ', 'M': 'ء', '<': '>', '>': '<', '?': '؟'
}

LEGACY_NORMAL = {
    '`': '`', '1': '۱', '2': '۲', '3': '۳', '4': '۴', '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹', '0': '۰', '-': '-', '=': '=',
    'q': 'ض', 'w': 'ص', 'e': 'ث', 'r': 'ق', 't': 'ف', 'y': 'غ', 'u': 'ع', 'i': 'ه', 'o': 'خ', 'p': 'ح', '[': 'ج', ']': 'چ', '\\': '\\',
    'a': 'ش', 's': 'س', 'd': 'ی', 'f': 'ب', 'g': 'ل', 'h': 'ا', 'j': 'ت', 'k': 'ن', 'l': 'م', ';': 'ک', "'": 'گ',
    'z': 'ظ', 'x': 'ط', 'c': 'ز', 'v': 'ر', 'b': 'ذ', 'n': 'د', 'm': 'پ', ',': 'و', '.': '.', '/': '/'
}

LEGACY_SHIFTED = {
    '~': '~', '!': '!', '@': '@', '#': '#', '$': '$', '%': '%', '^': '^', '&': '&', '*': '*', '(': ')', ')': '(', '_': '_', '+': '+',
    'Q': 'ً', 'W': 'ٌ', 'E': 'ٍ', 'R': '﷼', 'T': '،', 'Y': '؛', 'U': ',', 'I': ']', 'O': '[', 'P': '\\', '{': '}', '}': '{', '|': '|',
    'A': 'َ', 'S': 'ُ', 'D': 'ِ', 'F': 'ّ', 'G': 'ة', 'H': 'آ', 'J': 'ـ', 'K': '»', 'L': '«', ':': ':', '"': '"',
    'Z': 'ژ', 'X': 'ط', 'C': 'ژ', 'V': '\u200c', 'B': '\u200c', 'N': 'أ', 'M': 'ء', '<': '>', '>': '<', '?': '؟'
}

KEY_LABELS_EN = {
    'q': 'Q (ض)', 'w': 'W (ص)', 'e': 'E (ث)', 'r': 'R (ق)', 't': 'T (ف)', 'y': 'Y (غ)', 'u': 'U (ع)',
    'i': 'I (ه)', 'o': 'O (خ)', 'p': 'P (ح)', '[': '[ (ج)', ']': '] (چ)', '\\': '\\ (پ/\\)',
    'a': 'A (ش)', 's': 'S (س)', 'd': 'D (ی)', 'f': 'F (ب)', 'g': 'G (ل)', 'h': 'H (ا)', 'j': 'J (ت)',
    'k': 'K (ن)', 'l': 'L (م)', ';': '; (ک)', "'": "' (گ)",
    'z': 'Z (ظ)', 'x': 'X (ط)', 'c': 'C (ز)', 'v': 'V (ر)', 'b': 'B (ذ)', 'n': 'N (د)', 'm': 'M (ئ/پ)',
    ',': ', (و)', '.': '. (.)', '/': '/ (/)', '`': '` (ZWNJ / پ)',
    '1': '1 (۱)', '2': '2 (۲)', '3': '3 (۳)', '4': '4 (۴)', '5': '5 (۵)',
    '6': '6 (۶)', '7': '7 (۷)', '8': '8 (۸)', '9': '9 (۹)', '0': '0 (۰)',
    '-': '- (-)', '=': '= (=)'
}

SHIFT_LABELS_EN = {
    'C': 'Shift + C (ژ - Zhe)', 'Z': 'Shift + Z (ك / ژ)', 'V': 'Shift + V (ZWNJ / نیم‌فاصله)',
    'H': 'Shift + H (آ - Alef Madda)', 'T': 'Shift + T (، - Persian Comma)', 'Y': 'Shift + Y (؛ - Persian Semicolon)', '?': 'Shift + / (؟ - Question Mark)',
    'A': 'Shift + A (َ - Fatha)', 'S': 'Shift + S (ُ - Damma)', 'D': 'Shift + D (ِ - Kasra)', 'F': 'Shift + F (ّ - Tashdid)',
    'G': 'Shift + G (ۀ / ة)', 'J': 'Shift + J (ـ - Tatweel)', 'K': 'Shift + K (« - Quotation)', 'L': 'Shift + L (» - Quotation)',
    'B': 'Shift + B (إ / «)', 'N': 'Shift + N (أ / »)', 'M': 'Shift + M (ء - Hamza)',
    'Q': 'Shift + Q (ً - Tanwin)', 'W': 'Shift + W (ٌ - Tanwin)', 'E': 'Shift + E (ٍ - Tanwin)', 'R': 'Shift + R (ْ / ﷼)',
    'I': 'Shift + I (])', 'O': 'Shift + O ([)', '{': 'Shift + [ (})', '}': 'Shift + ] ({)',
    '~': 'Shift + ` (÷ / ~)', '!': 'Shift + 1 (!)', '@': 'Shift + 2 (٬ / @)', '#': 'Shift + 3 (٫ / #)',
    '$': 'Shift + 4 (﷼ / $)', '%': 'Shift + 5 (٪ / %)', '^': 'Shift + 6 (× / ^)', '&': 'Shift + 7 (، / &)',
    '*': 'Shift + 8 (*)', '(': 'Shift + 9 ())', ')': 'Shift + 0 (()', '_': 'Shift + - (_)', '+': 'Shift + = (+)'
}

KEY_LABELS = KEY_LABELS_EN
SHIFT_LABELS = SHIFT_LABELS_EN


# ==========================================
# PURE WIN32 INPUT HELPERS
# ==========================================

def _win32_key_down(vk):
    scan = user32.MapVirtualKeyW(vk, 0)
    flags = KEYEVENTF_EXTENDEDKEY if vk in [VK_LEFT, VK_RIGHT] else 0
    user32.keybd_event(vk, scan, flags, 0)


def _win32_key_up(vk):
    scan = user32.MapVirtualKeyW(vk, 0)
    flags = (KEYEVENTF_EXTENDEDKEY if vk in [VK_LEFT, VK_RIGHT] else 0) | KEYEVENTF_KEYUP
    user32.keybd_event(vk, scan, flags, 0)


def _wait_for_hotkey_release():
    """Waits up to 150ms for physical Ctrl, Shift, Alt, Space keys to be released."""
    for _ in range(15):
        is_held = any(
            (user32.GetAsyncKeyState(k) & 0x8000) != 0
            for k in [VK_CONTROL, VK_SHIFT, VK_MENU, VK_SPACE]
        )
        if not is_held:
            break
        time.sleep(0.01)
    
    _win32_key_up(VK_CONTROL)
    _win32_key_up(VK_SHIFT)
    _win32_key_up(VK_MENU)
    _win32_key_up(VK_SPACE)
    time.sleep(0.01)


def _win32_copy():
    """Copies current selection using standard Win32 Ctrl+C."""
    _win32_key_down(VK_CONTROL)
    time.sleep(0.015)
    _win32_key_down(VK_C)
    time.sleep(0.02)
    _win32_key_up(VK_C)
    time.sleep(0.015)
    _win32_key_up(VK_CONTROL)


def _win32_paste():
    """Pastes using standard Win32 Ctrl+V."""
    _win32_key_down(VK_CONTROL)
    time.sleep(0.015)
    _win32_key_down(VK_V)
    time.sleep(0.02)
    _win32_key_up(VK_V)
    time.sleep(0.015)
    _win32_key_up(VK_CONTROL)


def _win32_select_word_and_copy(direction="left"):
    """
    Selects previous word using Ctrl+Shift+(Left or Right Arrow)
    without dropping modifier state, then copies it immediately.
    - direction="left": used for LTR text (English)
    - direction="right": used for RTL text (Persian)
    """
    dir_vk = VK_LEFT if direction == "left" else VK_RIGHT

    _win32_key_down(VK_CONTROL)
    time.sleep(0.015)
    _win32_key_down(VK_SHIFT)
    time.sleep(0.015)
    
    # Tap arrow key (Extended Key)
    _win32_key_down(dir_vk)
    time.sleep(0.025)
    _win32_key_up(dir_vk)
    time.sleep(0.015)
    
    # Release Shift (Keep Ctrl held!)
    _win32_key_up(VK_SHIFT)
    time.sleep(0.015)
    
    # Tap C (Ctrl+C)
    _win32_key_down(VK_C)
    time.sleep(0.025)
    _win32_key_up(VK_C)
    time.sleep(0.015)
    
    # Release Ctrl
    _win32_key_up(VK_CONTROL)


def _win32_unselect(direction="left"):
    """
    Taps arrow key to cancel any active selection and restore cursor position.
    """
    # If we selected left, tap right to restore cursor
    # If we selected right, tap left to restore cursor
    unsel_vk = VK_RIGHT if direction == "left" else VK_LEFT
    _win32_key_down(unsel_vk)
    time.sleep(0.015)
    _win32_key_up(unsel_vk)


# ==========================================
# KEYBOARD ENGINE CLASS
# ==========================================

class KeyboardEngine:
    def __init__(self, preset="standard", custom_normal=None, custom_shifted=None, normalize_arabic=True):
        self.preset = preset
        self.custom_normal = custom_normal or {}
        self.custom_shifted = custom_shifted or {}
        self.normalize_arabic = normalize_arabic
        self.en_to_fa = {}
        self.fa_to_en = {}
        self.rebuild_maps()

    def rebuild_maps(self):
        """Builds forward and reverse character maps."""
        if self.preset == "legacy":
            base_normal = LEGACY_NORMAL.copy()
            base_shifted = LEGACY_SHIFTED.copy()
        else:
            base_normal = STANDARD_NORMAL.copy()
            base_shifted = STANDARD_SHIFTED.copy()

        base_normal.update(self.custom_normal)
        base_shifted.update(self.custom_shifted)

        self.active_normal = base_normal
        self.active_shifted = base_shifted

        self.en_to_fa = {**base_normal, **base_shifted}
        self.fa_to_en = {}

        for en_k, fa_v in base_normal.items():
            if fa_v not in self.fa_to_en:
                self.fa_to_en[fa_v] = en_k

        for en_k, fa_v in base_shifted.items():
            if fa_v in ['ژ', 'آ', '\u200c', '،', '؛', '؟', '«', '»', 'ء', 'أ', 'إ', 'ۀ', 'ة', 'ـ', 'َ', 'ُ', 'ِ', 'ّ', 'ً', 'ٌ', 'ٍ', 'ْ', '﷼', '٪', '×']:
                self.fa_to_en[fa_v] = en_k
            elif fa_v not in self.fa_to_en:
                self.fa_to_en[fa_v] = en_k

    def detect_direction(self, text: str) -> str:
        """Determines whether text is primarily English or Persian."""
        en_score = 0
        fa_score = 0
        for ch in text:
            if ch in self.en_to_fa and ch.isascii() and (ch.isalpha() or ch in ";':,./[]\\`"):
                en_score += 1
            if ch in self.fa_to_en and not ch.isascii():
                fa_score += 1

        return 'to_fa' if en_score >= fa_score else 'to_en'

    def convert_text(self, text: str, force_direction=None) -> tuple[str, str]:
        """Converts text between Persian and English."""
        direction = force_direction or self.detect_direction(text)
        
        if direction == 'to_fa':
            result = ''.join(self.en_to_fa.get(ch, ch) for ch in text)
            if self.normalize_arabic:
                result = result.replace('\u064A', '\u06CC').replace('\u0643', '\u06A9')
            return result, 'fa'
        else:
            norm_text = text.replace('\u064A', '\u06CC').replace('\u0643', '\u06A9')
            result = ''.join(self.fa_to_en.get(ch, ch) for ch in norm_text)
            return result, 'en'

    @staticmethod
    def get_current_keyboard_language() -> str:
        """
        Detects whether active foreground window (or thread) is Persian (0x0429) or English (0x0409).
        Returns 'fa' or 'en'.
        """
        try:
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                tid = user32.GetWindowThreadProcessId(hwnd, None)
                hkl = user32.GetKeyboardLayout(tid)
                lang_id = hkl & 0xFFFF
                if lang_id in [0x0429, 0x0401]:
                    return "fa"
                elif lang_id == 0x0409:
                    return "en"
        except Exception:
            pass
        try:
            hkl = user32.GetKeyboardLayout(0)
            lang_id = hkl & 0xFFFF
            return "fa" if lang_id in [0x0429, 0x0401] else "en"
        except Exception:
            return "en"

    @staticmethod
    def play_sound(style: str):
        try:
            if style == "soft":
                winsound.Beep(1600, 30)
            elif style == "chime":
                winsound.Beep(1200, 35)
                winsound.Beep(1800, 55)
            elif style == "beep":
                winsound.MessageBeep(winsound.MB_OK)
        except Exception:
            pass

    @staticmethod
    def switch_windows_layout(target_lang: str) -> bool:
        """Switches the active Windows keyboard layout."""
        try:
            hkl_id = "00000429" if target_lang == "fa" else "00000409"
            hkl = user32.LoadKeyboardLayoutW(hkl_id, KLF_ACTIVATE | KLF_SETFORPROCESS)
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                user32.PostMessageW(hwnd, WM_INPUTLANGCHANGEREQUEST, 0, hkl)
            user32.ActivateKeyboardLayout(hkl, 0)
            return True
        except Exception as e:
            print(f"[Engine] Layout switch error: {e}")
            return False

    def _capture_word_in_direction(self, direction: str, sentinel: str) -> str:
        """Attempts to select and copy word in the specified direction (left or right)."""
        pyperclip.copy(sentinel)
        time.sleep(0.015)
        _win32_select_word_and_copy(direction)

        word = ""
        for _ in range(6):
            time.sleep(0.02)
            try:
                cur = pyperclip.paste()
                if cur != sentinel:
                    word = cur
                    break
            except Exception:
                pass

        # If only space was selected (trailing whitespace), select one more word!
        if word and word.isspace():
            _win32_select_word_and_copy(direction)
            for _ in range(6):
                time.sleep(0.02)
                try:
                    cur = pyperclip.paste()
                    if cur != sentinel and cur != word:
                        word = cur
                        break
                except Exception:
                    pass

        if word and word != sentinel and word.strip():
            return word

        # If nothing valid was captured, unselect to restore cursor position
        _win32_unselect(direction)
        return ""

    def fix_selection(self, auto_switch=True, sound_style="soft", restore_clip=True, smart_word_select=True) -> dict:
        """
        Rock-solid bidirectional in-place text replacement:
        1. Waits for physical hotkey keys (Ctrl, Space, Shift) to release.
        2. Tries to copy active selection (Ctrl+C).
        3. If no selection exists, uses direction-aware smart word selection:
           - In Persian (RTL text), previous word is to the RIGHT (Ctrl+Shift+Right).
           - In English (LTR text), previous word is to the LEFT (Ctrl+Shift+Left).
           - Includes automatic fallback if editor has opposing direction.
        4. Converts text, pastes back (Ctrl+V).
        5. Switches layout & plays audio feedback.
        """
        try:
            # 1. Wait for physical keys to release so they don't interfere
            _wait_for_hotkey_release()

            # Save existing clipboard
            try:
                original_clipboard = pyperclip.paste()
            except Exception:
                original_clipboard = ""

            sentinel = f"__KBFIX_{time.time()}__"
            pyperclip.copy(sentinel)
            time.sleep(0.02)

            # 2. Try copying explicit selection first
            _win32_copy()
            
            selected_text = ""
            for _ in range(6):
                time.sleep(0.02)
                try:
                    cur = pyperclip.paste()
                    if cur != sentinel:
                        selected_text = cur
                        break
                except Exception:
                    pass

            used_smart_word = False

            # 3. Smart word selection fallback if nothing was manually selected
            if (not selected_text or selected_text == sentinel or not selected_text.strip()) and smart_word_select:
                used_smart_word = True
                
                # Detect active language to choose correct RTL vs LTR selection direction
                cur_lang = self.get_current_keyboard_language()
                
                # In RTL Persian, typed word is to the RIGHT of cursor.
                # In LTR English, typed word is to the LEFT of cursor.
                primary_dir = "right" if cur_lang == "fa" else "left"
                fallback_dir = "left" if primary_dir == "right" else "right"

                # Try primary direction
                captured = self._capture_word_in_direction(primary_dir, sentinel)
                
                # If primary direction got nothing, try opposite direction (e.g. LTR field in Persian)
                if not captured:
                    captured = self._capture_word_in_direction(fallback_dir, sentinel)

                selected_text = captured

            # Check if valid text was captured
            if not selected_text or selected_text == sentinel or not selected_text.strip():
                pyperclip.copy(original_clipboard)
                return {"success": False}

            # Convert text
            converted_text, target_lang = self.convert_text(selected_text)
            
            if converted_text == selected_text:
                pyperclip.copy(original_clipboard)
                return {"success": False}

            # Paste converted text
            pyperclip.copy(converted_text)
            time.sleep(0.03)
            _win32_paste()
            time.sleep(0.04)

            # Switch layout
            if auto_switch:
                self.switch_windows_layout(target_lang)

            # Audio
            if sound_style != "none":
                self.play_sound(sound_style)

            # Restore original clipboard
            if restore_clip and original_clipboard != sentinel:
                time.sleep(0.35)
                pyperclip.copy(original_clipboard)

            return {
                "success": True,
                "original": selected_text,
                "converted": converted_text,
                "target_lang": target_lang,
                "word_count": max(1, len(selected_text.split()))
            }

        except Exception as e:
            print(f"[Engine] fix_selection error: {e}")
            return {"success": False, "error": str(e)}
