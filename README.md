# Clock In/Out Reminder

A cross-platform desktop application built in Python using Tkinter that reminds you when to clock in and clock out. The app features notifications, an animated dinosaur, a live countdown timer until your next clock in/out event, and configurable settings.

## Features

- **Countdown Timer:** Displays a live countdown until the next clock in/out event.
- **Custom Notifications:** Sends system notifications using platform-specific methods (win10toast on Windows, osascript on macOS, notify-send on Linux). The notification window is forced to the foreground.
- **Animated UI:** Includes a fun animated dinosaur and an animated progress bar.
- **User Settings:** Configure your clock in/out times, select time format (12-hour or 24-hour), and choose a time zone (if pytz is installed).
- **Preset Management:** Save and load your clock in/out presets.
- **Scrollable Interface:** The app uses a scrollable area to accommodate all UI elements on smaller screens.

## Installation

### Prerequisites

- **Python 3.x**  
- **Tkinter** (usually comes with Python on Windows and macOS)

### Required Python Packages

The app requires the following packages:
- `pytz` (optional – enhances timezone support)
- `Pillow` (for icon creation)
- `pystray` (for system tray functionality)
- `win10toast` (for notifications on Windows)

### Installing Dependencies

Install the dependencies using pip:

```bash
pip install pytz pillow pystray win10toast
