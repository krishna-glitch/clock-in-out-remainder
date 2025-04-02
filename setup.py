#!/usr/bin/env python3
# setup.py - Setup script for Clock Reminder
# This script checks dependencies and creates necessary files for the app to run

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

PLATFORM = platform.system().lower()  # 'windows', 'darwin' (macOS), or 'linux'

def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 60)
    print(f" {message}")
    print("=" * 60)

def check_python_version():
    """Check if Python version is compatible."""
    print_header("Checking Python version")
    
    major, minor = sys.version_info[:2]
    print(f"Detected Python {major}.{minor}")
    
    if major < 3 or (major == 3 and minor < 6):
        print("ERROR: Python 3.6 or higher is required")
        return False
    else:
        print("Python version OK")
        return True

def install_dependencies():
    """Install required packages."""
    print_header("Installing dependencies")
    
    # Basic dependencies for all platforms
    dependencies = ["pillow", "pytz"]
    
    # Platform-specific dependencies
    if PLATFORM == 'windows':
        dependencies.append("pystray")
    elif PLATFORM == 'darwin':  # macOS
        dependencies.append("rumps")
    elif PLATFORM == 'linux':
        dependencies.extend(["pystray", "PyGObject"])
    
    # Install using pip
    for package in dependencies:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"{package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"WARNING: Failed to install {package}")
    
    return True

def create_launcher():
    """Create platform-specific launcher."""
    print_header("Creating launcher")
    
    script_dir = Path(__file__).parent.absolute()
    
    if PLATFORM == 'windows':
        # Create a Windows .bat file
        bat_path = script_dir / "run_reminder.bat"
        with open(bat_path, "w") as f:
            f.write(f'@echo off\n"{sys.executable}" "{script_dir / "reminder.py"}"\n')
        print(f"Created Windows launcher: {bat_path}")
        
        # Create a shortcut if possible
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "Clock Reminder.lnk")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = str(bat_path)
            shortcut.WorkingDirectory = str(script_dir)
            icon_path = script_dir / "clock.ico"
            if icon_path.exists():
                shortcut.IconLocation = str(icon_path)
            shortcut.save()
            
            print(f"Created desktop shortcut: {shortcut_path}")
        except ImportError:
            print("Note: pywin32 and winshell not installed; skipping desktop shortcut creation")
        except Exception as e:
            print(f"Warning: Could not create shortcut: {e}")
            
    elif PLATFORM == 'darwin':  # macOS
        # Create an applescript file
        app_script_path = script_dir / "run_reminder.scpt"
        python_path = sys.executable
        reminder_path = script_dir / "reminder.py"
        
        with open(app_script_path, "w") as f:
            f.write(f'''
tell application "Terminal"
    do script "{python_path} {reminder_path}"
end tell
''')
        
        # Make it executable
        os.chmod(app_script_path, 0o755)
        print(f"Created macOS launcher: {app_script_path}")
        
        # Create an Application bundle if py2app is available
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "py2app"])
            setup_py_path = script_dir / "setup_app.py"
            
            with open(setup_py_path, "w") as f:
                f.write(f'''
from setuptools import setup

APP = ['{reminder_path}']
DATA_FILES = []
OPTIONS = {{
    'argv_emulation': True,
    'iconfile': '{script_dir}/clock.icns' if os.path.exists('{script_dir}/clock.icns') else None,
    'plist': {{
        'CFBundleName': 'Clock Reminder',
        'CFBundleDisplayName': 'Clock Reminder',
        'CFBundleIdentifier': 'com.clockreminder.app',
        'CFBundleVersion': '1.0.0',
        'CFBundlePackageType': 'APPL',
        'LSMinimumSystemVersion': '10.10',
        'NSHumanReadableCopyright': 'Copyright © 2025'
    }}
}}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={{'py2app': OPTIONS}},
    setup_requires=['py2app'],
)
''')
            
            # Run py2app
            subprocess.check_call([sys.executable, "setup_app.py", "py2app"], cwd=str(script_dir))
            print("Created macOS app bundle in 'dist' folder")
            
        except Exception as e:
            print(f"Warning: Could not create app bundle: {e}")
            
    elif PLATFORM == 'linux':
        # Create a shell script
        sh_path = script_dir / "run_reminder.sh"
        with open(sh_path, "w") as f:
            f.write(f'''#!/bin/bash
"{sys.executable}" "{script_dir / "reminder.py"}"
''')
        # Make it executable
        os.chmod(sh_path, 0o755)
        print(f"Created Linux launcher: {sh_path}")
        
        # Create a desktop entry
        desktop_path = script_dir / "clock-reminder.desktop"
        icon_path = script_dir / "clock.png"
        
        with open(desktop_path, "w") as f:
            f.write(f'''[Desktop Entry]
Name=Clock Reminder
Comment=Reminder app for clock in/out times
Exec={sh_path}
Icon={icon_path if icon_path.exists() else ''}
Terminal=false
Type=Application
Categories=Utility;
''')
        
        # Try to install desktop entry
        try:
            user_apps_dir = Path.home() / ".local" / "share" / "applications"
            user_apps_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(desktop_path, user_apps_dir / "clock-reminder.desktop")
            print(f"Installed desktop entry to {user_apps_dir}")
        except Exception as e:
            print(f"Warning: Could not install desktop entry: {e}")
    
    print("Launcher created successfully")
    return True

def create_default_icon():
    """Create a default icon if none exists."""
    print_header("Creating default icon")
    
    script_dir = Path(__file__).parent.absolute()
    
    # Check if any icon already exists
    if PLATFORM == 'windows' and (script_dir / "clock.ico").exists():
        print("Icon already exists")
        return True
    elif PLATFORM == 'darwin' and (script_dir / "clock.icns").exists():
        print("Icon already exists")
        return True
    elif PLATFORM == 'linux' and (script_dir / "clock.png").exists():
        print("Icon already exists")
        return True
    
    # Try to create a basic icon
    try:
        from PIL import Image, ImageDraw
        
        # Create a simple icon - green square with a clock shape
        width, height = 256, 256
        image = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a circle for the clock face (light gray)
        draw.ellipse((40, 40, width-40, height-40), fill=(237, 244, 242, 255), outline=(49, 71, 58, 255), width=5)
        
        # Draw clock hands
        center_x, center_y = width // 2, height // 2
        
        # Hour hand (shorter)
        hour_hand_length = 60
        hour_hand_end_x = center_x
        hour_hand_end_y = center_y - hour_hand_length
        draw.line((center_x, center_y, hour_hand_end_x, hour_hand_end_y), fill=(49, 71, 58, 255), width=10)
        
        # Minute hand (longer)
        minute_hand_length = 90
        minute_hand_end_x = center_x + minute_hand_length // 2
        minute_hand_end_y = center_y + minute_hand_length // 2
        draw.line((center_x, center_y, minute_hand_end_x, minute_hand_end_y), fill=(49, 71, 58, 255), width=8)
        
        # Draw center dot
        draw.ellipse((center_x-10, center_y-10, center_x+10, center_y+10), fill=(49, 71, 58, 255))
        
        # Save in appropriate format for the platform
        if PLATFORM == 'windows':
            # Windows needs .ico format
            image.save(script_dir / "clock.ico", format="ICO")
            print("Created Windows icon: clock.ico")
        elif PLATFORM == 'darwin':
            # macOS uses .icns but it's complex to create, so use PNG as fallback
            image.save(script_dir / "clock.png", format="PNG")
            print("Created macOS icon: clock.png")
            
            # Try to convert to .icns if iconutil is available (macOS only)
            try:
                iconset_dir = script_dir / "clock.iconset"
                iconset_dir.mkdir(exist_ok=True)
                
                # Create various sizes required for .icns
                sizes = [16, 32, 64, 128, 256, 512]
                for size in sizes:
                    resized = image.resize((size, size), Image.LANCZOS)
                    resized.save(iconset_dir / f"icon_{size}x{size}.png")
                    # Also save the 2x version
                    if size * 2 <= 512:  # Don't exceed 1024x1024
                        resized = image.resize((size*2, size*2), Image.LANCZOS)
                        resized.save(iconset_dir / f"icon_{size}x{size}@2x.png")
                
                # Use iconutil to convert to .icns
                subprocess.check_call(["iconutil", "-c", "icns", str(iconset_dir)], cwd=str(script_dir))
                print("Created macOS icon: clock.icns")
                
                # Clean up
                shutil.rmtree(iconset_dir)
                
            except (FileNotFoundError, subprocess.CalledProcessError):
                print("Could not create .icns file, PNG will be used instead")
                
        elif PLATFORM == 'linux':
            # Linux uses PNG
            image.save(script_dir / "clock.png", format="PNG")
            print("Created Linux icon: clock.png")
        
        return True
        
    except ImportError:
        print("Warning: Pillow not installed, skipping icon creation")
        return False
    except Exception as e:
        print(f"Warning: Could not create icon: {e}")
        return False

def main():
    """Main function to run the setup."""
    print_header("Clock Reminder Setup")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    install_dependencies()
    
    # Create default icon
    create_default_icon()
    
    # Create launcher
    create_launcher()
    
    print_header("Setup complete!")
    print("You can now run the Clock Reminder application using the created launcher.")
    print("Enjoy your productive day!")

if __name__ == "__main__":
    main()