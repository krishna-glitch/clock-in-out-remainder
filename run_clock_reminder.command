#!/bin/bash
# run_clock_reminder.command - macOS launcher for Clock Reminder

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment if it exists
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
    echo "Activated virtual environment"
fi

# Run the application
python3 "$SCRIPT_DIR/simple_macos_reminder.py"

# Keep terminal window open on error
if [ $? -ne 0 ]; then
    echo ""
    echo "====================================="
    echo "Error running the application"
    echo "Press Enter to close this window..."
    read
fi