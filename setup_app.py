
from setuptools import setup

APP = ['/Users/krishnadasyam/Documents/clock-in-out-remainder/reminder.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'iconfile': '/Users/krishnadasyam/Documents/clock-in-out-remainder/clock.icns' if os.path.exists('/Users/krishnadasyam/Documents/clock-in-out-remainder/clock.icns') else None,
    'plist': {
        'CFBundleName': 'Clock Reminder',
        'CFBundleDisplayName': 'Clock Reminder',
        'CFBundleIdentifier': 'com.clockreminder.app',
        'CFBundleVersion': '1.0.0',
        'CFBundlePackageType': 'APPL',
        'LSMinimumSystemVersion': '10.10',
        'NSHumanReadableCopyright': 'Copyright © 2025'
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
