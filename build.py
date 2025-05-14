#!/usr/bin/env python3
"""
QDMBoxSearch Build Script
-------------------------
Build script for creating standalone executables for macOS, Windows, and Linux.
Author: J.F. Durocher
Copyright (c) 2025 J.F. Durocher (jf@durocher.in)
"""

import os
import sys
import platform
import subprocess
import shutil
from datetime import datetime

def run_command(command):
    """Run a shell command and print its output."""
    print(f"Running: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in process.stdout:
        print(line.decode().strip())
    process.wait()
    return process.returncode

def build_for_platform():
    """Build the application for the current platform."""
    system = platform.system().lower()
    
    # Clean previous builds
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # Set icon based on platform
    if system == "darwin":
        icon = "icon.icns"
    elif system == "windows":
        icon = "icon.ico"
    else:
        icon = "icon.png"
    
    # Build command
    cmd = f"pyinstaller --windowed --name QDMBoxSearch --icon={icon} mbox_search_gui.py"
    
    # Run the build
    if run_command(cmd) != 0:
        print(f"Error building for {system}")
        return False
    
    # Create version file
    version = datetime.now().strftime("%Y.%m.%d")
    with open("dist/QDMBoxSearch/version.txt", "w") as f:
        f.write(f"QDMBoxSearch v{version}\n")
        f.write(f"Built on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Platform: {system}\n")
    
    # Copy LICENSE
    shutil.copy("LICENSE", "dist/QDMBoxSearch/")
    
    print(f"\nBuild completed for {system}")
    print(f"Output directory: {os.path.abspath('dist/QDMBoxSearch')}")
    return True

def main():
    """Main function to run the build process."""
    print("QDMBoxSearch Build Script")
    print("------------------------")
    print(f"Building for: {platform.system()}")
    
    if build_for_platform():
        print("\nBuild successful!")
    else:
        print("\nBuild failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 