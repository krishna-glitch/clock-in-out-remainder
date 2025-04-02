#!/usr/bin/env python3
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
        exec(open('/Users/krishnadasyam/Documents/clock-in-out-remainder/reminder.py').read())
