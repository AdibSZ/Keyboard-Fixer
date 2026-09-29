"""
Build script to compile Keyboard Fixer into a standalone Windows .exe using PyInstaller.
"""
import subprocess
import sys
import os

def build():
    print("Building Keyboard Fixer executable...")
    icon_path = os.path.join("assets", "icon.ico")
    
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name=KeyboardFixer",
        f"--icon={icon_path}",
        "--add-data=assets;assets",
        "main.py"
    ]
    
    print("Running command:", " ".join(cmd))
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print("\n [SUCCESS] KeyboardFixer.exe has been built successfully in the 'dist' folder!")
    else:
        print("\n [ERROR] Build failed. See logs above.")

if __name__ == "__main__":
    build()
