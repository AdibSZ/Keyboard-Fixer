"""
Test script to verify keyboard_engine conversion accuracy.
"""
import sys
if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')
from keyboard_engine import KeyboardEngine

def test_engine():
    engine = KeyboardEngine(preset="standard")

    test_cases = [
        ("sghl", "سلام", "fa"),
        ("سلام", "sghl", "en"),
        (";df,vn", "کیبورد", "fa"),
        ("کیبورد", ";df,vn", "en"),
        ("Cghl", "ژلام", "fa"),          # Shift + C = ژ
        ("ژلام", "Cghl", "en"),
        ("Hclhda", "آزمایش", "fa"),       # Shift + H = آ
        ("آزمایش", "Hclhda", "en"),
        ("d;sVn,", "یکس‌دو", "fa"),      # Shift + V = نیم‌فاصله
        ("یکس‌دو", "d;sVn,", "en"),
        ("]x,vd?", "چطوری؟", "fa"),     # ]=چ, x=ط, ,=و, v=ر, d=ی, ?=؟
        ("چطوری؟", "]x,vd?", "en"),
        ("T", "،", "fa"),                 # Shift + T = ،
        ("،", "T", "en"),
    ]

    all_passed = True
    for inp, expected, expected_lang in test_cases:
        actual, lang = engine.convert_text(inp)
        if actual == expected and lang == expected_lang:
            print(f" PASS: '{inp}' -> '{actual}' ({lang})")
        else:
            print(f" FAIL: '{inp}' -> Got '{actual}' ({lang}), Expected '{expected}' ({expected_lang})")
            all_passed = False

    if all_passed:
        print("\n ALL TESTS PASSED SUCCESSFULLY!")
    else:
        print("\n SOME TESTS FAILED!")

if __name__ == "__main__":
    test_engine()
