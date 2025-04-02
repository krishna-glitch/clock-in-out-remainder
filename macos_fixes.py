#!/usr/bin/env python3
# macos_fixes.py - Helper script for macOS-specific fixes

import sys
import os
import subprocess
from pathlib import Path

def create_app_nib():
    """Create a basic .nib file for macOS app to properly handle Dock interaction."""
    script_dir = Path(__file__).parent.absolute()
    
    # Create Info.plist
    info_plist_path = script_dir / "Info.plist"
    info_plist_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>English</string>
    <key>CFBundleExecutable</key>
    <string>clock_reminder</string>
    <key>CFBundleIconFile</key>
    <string>clock.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.example.clockreminder</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Clock Reminder</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSSupportsAutomaticGraphicsSwitching</key>
    <true/>
</dict>
</plist>
'''
    
    with open(info_plist_path, "w") as f:
        f.write(info_plist_content)
    
    print(f"Created Info.plist at {info_plist_path}")
    
    # Create a simple AppleScript to handle notifications
    notification_helper_path = script_dir / "notification_helper.scpt"
    notification_helper_content = '''
on run argv
    set titleText to item 1 of argv
    set messageText to item 2 of argv
    
    display notification messageText with title titleText
end run
'''
    
    with open(notification_helper_path, "w") as f:
        f.write(notification_helper_content)
        
    # Compile AppleScript
    try:
        subprocess.run(["osacompile", "-o", str(script_dir / "notification_helper.scpt"), 
                      str(notification_helper_path)])
        print("Created notification helper script")
    except:
        print("Warning: Could not compile AppleScript helper")
    
    # Create a wrapper script for launching the app with proper macOS support
    wrapper_script_path = script_dir / "clock_reminder_mac.py"
    main_script_path = script_dir / "reminder.py"
    
    wrapper_content = f'''#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

# Add dock icon support - must happen before Tkinter is imported
try:
    from AppKit import NSApplication
    app = NSApplication.sharedApplication()
except:
    pass

# Import main script
script_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(script_dir))

# Function to send notifications using AppleScript
def notify(title, message):
    helper_script = script_dir / "notification_helper.scpt"
    if helper_script.exists():
        try:
            subprocess.run(["osascript", str(helper_script), title, message])
            return True
        except:
            return False
    return False

# Patch sys.modules to include our notification function
class MacOSHelper:
    @staticmethod
    def send_notification(title, message):
        return notify(title, message)

sys.modules['macos_helper'] = MacOSHelper

# Import and run the main app
if __name__ == "__main__":
    try:
        import reminder
        reminder.main()
    except ImportError:
        # Try to execute the script directly if import fails
        exec(open('{main_script_path}').read())
'''
    
    with open(wrapper_script_path, "w") as f:
        f.write(wrapper_content)
    
    # Make it executable
    os.chmod(wrapper_script_path, 0o755)
    
    print(f"Created macOS wrapper script at {wrapper_script_path}")
    return wrapper_script_path

def fix_macos_app_settings():
    """Apply macOS-specific fixes."""
    # Create .nib file and wrapper
    wrapper_path = create_app_nib()
    
    # Create a simple launcher shell script
    script_dir = Path(__file__).parent.absolute()
    launcher_path = script_dir / "run_clock_reminder.command"
    
    with open(launcher_path, "w") as f:
        f.write(f'''#!/bin/bash
cd "$(dirname "$0")"
python3 "{wrapper_path}"
''')
    
    # Make it executable
    os.chmod(launcher_path, 0o755)
    
    print(f"Created macOS launcher at {launcher_path}")
    print("You can now run the application by double-clicking this file in Finder.")
    
    # Create a Dock-friendly launcher app if platypus is installed
    try:
        if subprocess.run(["which", "platypus"], capture_output=True).returncode == 0:
            app_path = script_dir / "Clock Reminder.app"
            icon_path = script_dir / "clock.icns"
            if not icon_path.exists():
                icon_path = script_dir / "clock.png"
                
            subprocess.run([
                "platypus", 
                "-a", "Clock Reminder",
                "-o", "Text Window",
                "-p", "/usr/bin/python3",
                "-V", "1.0",
                "-I", "com.example.clockreminder",
                "-i", str(icon_path) if icon_path.exists() else "",
                "-f", str(wrapper_path),
                str(app_path)
            ])
            
            print(f"Created macOS app bundle at {app_path}")
    except:
        print("Note: Platypus not found. If you want to create a .app bundle, install Platypus with 'brew install platypus'")

if __name__ == "__main__":
    fix_macos_app_settings()