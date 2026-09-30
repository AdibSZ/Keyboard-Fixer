"""
Build script to compile Keyboard Fixer into a standalone Windows .exe using PyInstaller.
"""
import subprocess
import sys
import os
import shutil

# Reconfigure stdout/stderr to utf-8 if supported
if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def build():
    print("=" * 60)
    print("[BUILD] Compiling Keyboard Fixer Pro to Standalone Windows Executable")
    print("=" * 60)
    
    icon_path = os.path.join("assets", "icon.ico")
    
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--clean",
        "--noconsole",
        "--onefile",
        "--name=KeyboardFixer",
        f"--icon={icon_path}",
        "--add-data=assets;assets",
        "--collect-all=customtkinter",
        "--collect-all=pystray",
        "--hidden-import=pystray._win32",
        "--hidden-import=keyboard",
        "--hidden-import=pyperclip",
        "--hidden-import=PIL",
        "main.py"
    ]
    
    print("\n[PyInstaller Command]:")
    print(" ".join(cmd))
    print("\nBuilding... Please wait (this may take 1-2 minutes)...\n")
    
    res = subprocess.run(cmd)
    if res.returncode == 0:
        exe_path = os.path.abspath(os.path.join("dist", "KeyboardFixer.exe"))
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print("=" * 60)
        print("[SUCCESS] KeyboardFixer.exe has been created successfully!")
        print(f"Location: {exe_path}")
        print(f"File Size: {size_mb:.1f} MB")
        print("=" * 60)
        return True
    else:
        print("\n[ERROR] Build failed. See logs above.")
        return False

if __name__ == "__main__":
    success = build()
    if not success:
        sys.exit(1)
