#!/usr/bin/env python3
# simple_macos_reminder.py - A simplified version for macOS

import tkinter as tk
from tkinter import messagebox, ttk
import time
import datetime
import json
import os
import sys
import threading
from pathlib import Path
import math
import random

# Try importing pytz
try:
    import pytz
except ImportError:
    print("pytz not installed. Timezone functionality will be limited.")
    pytz = None

class ClockReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Clock In/Out Reminder")
        self.root.geometry("500x550")
        self.root.resizable(False, False)
        
        # Get app directory and create data directory
        self.app_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = self.get_data_dir()
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Colors
        self.colors = {
            "primary": "#31473A",    # Dark green
            "background": "#EDF4F2", # Light gray
            "text": "#31473A",       # Dark green
        }
        
        self.root.configure(bg=self.colors["background"])
        
        # Configure fonts - use system default font
        self.font_family = "Arial"  # Default, works on macOS
        
        # Variables
        self.clock_in_time = tk.StringVar(value="09:00")
        self.clock_out_time = tk.StringVar(value="17:00")
        self.reminder_count = 0
        self.is_running = False
        self.reminder_thread = None
        self.time_format = tk.StringVar(value="24-hour")
        self.timezone = tk.StringVar(value="Local")
        self.animation_active = False
        self.dino_position = 0
        self.dino_direction = 1
        
        # Load saved data
        self.load_data()
        
        # Create UI
        self.create_background()
        self.create_widgets()
        self.start_animations()
        
        # Start reminder thread if app was previously running
        if self.is_running:
            self.start_reminders()

    def get_data_dir(self):
        """Get platform-specific data directory for app files"""
        # macOS: Use ~/Library/Application Support/ClockReminder
        return Path.home() / "Library" / "Application Support" / "ClockReminder"

    def create_background(self):
        """Create a simple light gray background"""
        self.canvas = tk.Canvas(self.root, width=500, height=550, 
                               bg=self.colors["background"], highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Create a frame on top of the canvas for widgets
        self.main_frame = tk.Frame(self.root, bg=self.colors["background"], highlightthickness=0)
        self.main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, relwidth=0.95, relheight=0.95)

    def draw_dinosaur(self):
        """Draw a pixelated dinosaur"""
        # Clear canvas
        self.dino_canvas.delete("all")
        
        # Pixel size
        pixel_size = 4
        
        # Dinosaur position (8x8 grid)
        x_pos = self.dino_position
        
        # Draw pixels for dinosaur
        dino_pixels = [
            # Body (darker green)
            (1, 3), (1, 4), (1, 5),
            (2, 2), (2, 3), (2, 4), (2, 5), (2, 6),
            (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7),
            (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6),
            (5, 2), (5, 3), (5, 4), (5, 5),
            # Eye (white)
            (3, 2),
            # Legs (dynamic based on position)
            (2, 7), (4, 7)
        ]
        
        # Alternate legs for walking animation
        leg_pixels = []
        if self.dino_position % 8 < 4:
            leg_pixels = [(2, 7), (4, 7)]
        else:
            leg_pixels = [(3, 7), (5, 7)]
        
        # Draw dinosaur body
        for px, py in dino_pixels:
            if (px, py) == (3, 2):  # Eye
                self.dino_canvas.create_rectangle(
                    (x_pos + px) * pixel_size, py * pixel_size,
                    (x_pos + px + 1) * pixel_size, (py + 1) * pixel_size,
                    fill='white', outline='')
            else:
                self.dino_canvas.create_rectangle(
                    (x_pos + px) * pixel_size, py * pixel_size,
                    (x_pos + px + 1) * pixel_size, (py + 1) * pixel_size,
                    fill=self.colors["primary"], outline='')
        
        # Draw legs
        for px, py in leg_pixels:
            self.dino_canvas.create_rectangle(
                (x_pos + px) * pixel_size, py * pixel_size,
                (x_pos + px + 1) * pixel_size, (py + 1) * pixel_size,
                fill=self.colors["primary"], outline='')
        
        # Draw some small pixels representing flying bits
        for _ in range(3):
            px = random.randint(10, 90)
            py = random.randint(10, 50)
            size = random.randint(1, 2)
            self.dino_canvas.create_rectangle(
                px, py, px + size, py + size,
                fill=self.colors["text"], outline='')

    def create_widgets(self):
        # Dinosaur Animation canvas
        self.dino_canvas = tk.Canvas(self.main_frame, width=100, height=60, 
                                    bg=self.colors["background"], highlightthickness=0)
        self.dino_canvas.pack(pady=(10, 5))
        
        # Draw initial dinosaur
        self.draw_dinosaur()
        
        # Title
        title_label = tk.Label(self.main_frame, text="Clock In/Out Reminder", 
                              font=(self.font_family, 18, "bold"), bg=self.colors["background"], 
                              fg=self.colors["primary"])
        title_label.pack(pady=(0, 15))
        
        # Create card-like container for settings
        settings_frame = tk.Frame(self.main_frame, bg='white', 
                                 relief=tk.RIDGE, bd=1)
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        # Add a subtle header
        settings_header = tk.Frame(settings_frame, bg=self.colors["primary"], height=8)
        settings_header.pack(fill="x")
        
        settings_title = tk.Label(settings_frame, text="Settings", font=(self.font_family, 12, "bold"), 
                                 bg='white', fg=self.colors["primary"])
        settings_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        # Inner padding frame
        settings_content = tk.Frame(settings_frame, bg='white', padx=15, pady=10)
        settings_content.pack(fill="x")
        
        # Time Format Settings
        format_frame = tk.Frame(settings_content, bg='white')
        format_frame.pack(fill="x", pady=5)
        
        tk.Label(format_frame, text="Time Format:", font=(self.font_family, 10, "bold"), 
                bg='white').pack(side=tk.LEFT, padx=5)
        
        format_options = ttk.Combobox(format_frame, textvariable=self.time_format, width=10)
        format_options['values'] = ('12-hour', '24-hour')
        format_options.pack(side=tk.LEFT, padx=5)
        format_options.bind("<<ComboboxSelected>>", self.update_time_format)
        
        # Timezone Settings
        timezone_frame = tk.Frame(settings_content, bg='white')
        timezone_frame.pack(fill="x", pady=5)
        
        tk.Label(timezone_frame, text="Time Zone:", font=(self.font_family, 10, "bold"), 
                bg='white').pack(side=tk.LEFT, padx=5)
        
        timezone_options = ttk.Combobox(timezone_frame, textvariable=self.timezone, width=25)
        
        # Only show timezone options if pytz is available
        if pytz:
            popular_timezones = ['Local', 'US/Eastern', 'US/Central', 'US/Mountain', 'US/Pacific', 
                               'Europe/London', 'Europe/Paris', 'Asia/Tokyo', 'Australia/Sydney']
            timezone_options['values'] = popular_timezones
        else:
            timezone_options['values'] = ['Local']
            self.timezone.set('Local')
            
        timezone_options.pack(side=tk.LEFT, padx=5)
        
        # Create card-like container for time inputs
        times_frame = tk.Frame(self.main_frame, bg='white', 
                              relief=tk.RIDGE, bd=1)
        times_frame.pack(fill="x", padx=10, pady=10)
        
        # Add a subtle header
        times_header = tk.Frame(times_frame, bg=self.colors["primary"], height=8)
        times_header.pack(fill="x")
        
        times_title = tk.Label(times_frame, text="Reminder Times", font=(self.font_family, 12, "bold"), 
                              bg='white', fg=self.colors["primary"])
        times_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        # Inner padding frame
        times_content = tk.Frame(times_frame, bg='white', padx=15, pady=10)
        times_content.pack(fill="x")
        
        # Clock In Frame
        clock_in_frame = tk.Frame(times_content, bg='white')
        clock_in_frame.pack(fill="x", pady=5)
        
        clock_in_label = tk.Label(clock_in_frame, text="Clock In Time:", font=(self.font_family, 10, "bold"), 
                                 bg='white')
        clock_in_label.pack(side=tk.LEFT, padx=5)
        
        self.clock_in_entry = tk.Entry(clock_in_frame, textvariable=self.clock_in_time, width=10,
                                      font=(self.font_family, 10), justify="center",
                                      relief=tk.SOLID, bd=1)
        self.clock_in_entry.pack(side=tk.LEFT, padx=5)
        
        self.clock_in_ampm = ttk.Combobox(clock_in_frame, values=['AM', 'PM'], width=5)
        self.clock_in_ampm.current(0)  # Default to AM
        
        # Only show AM/PM dropdown if in 12-hour mode
        if self.time_format.get() == '12-hour':
            self.clock_in_ampm.pack(side=tk.LEFT, padx=5)
        
        # Clock Out Frame
        clock_out_frame = tk.Frame(times_content, bg='white')
        clock_out_frame.pack(fill="x", pady=5)
        
        clock_out_label = tk.Label(clock_out_frame, text="Clock Out Time:", font=(self.font_family, 10, "bold"), 
                                  bg='white')
        clock_out_label.pack(side=tk.LEFT, padx=5)
        
        self.clock_out_entry = tk.Entry(clock_out_frame, textvariable=self.clock_out_time, width=10,
                                       font=(self.font_family, 10), justify="center",
                                       relief=tk.SOLID, bd=1)
        self.clock_out_entry.pack(side=tk.LEFT, padx=5)
        
        self.clock_out_ampm = ttk.Combobox(clock_out_frame, values=['AM', 'PM'], width=5)
        self.clock_out_ampm.current(1)  # Default to PM
        
        # Only show AM/PM dropdown if in 12-hour mode
        if self.time_format.get() == '12-hour':
            self.clock_out_ampm.pack(side=tk.LEFT, padx=5)
        
        # Save preset button
        save_button = tk.Button(
            times_content, 
            text="Save as Preset", 
            command=self.save_preset,
            bg=self.colors["primary"], 
            fg="white", 
            font=(self.font_family, 9),
            relief=tk.RAISED,
            bd=1
        )
        save_button.pack(pady=5)
        
        # Load presets dropdown
        preset_frame = tk.Frame(times_content, bg='white')
        preset_frame.pack(fill="x", pady=5)
        
        tk.Label(preset_frame, text="Load Preset:", font=(self.font_family, 10, "bold"), 
                bg='white').pack(side=tk.LEFT, padx=5)
        
        self.preset_var = tk.StringVar()
        self.preset_dropdown = ttk.Combobox(preset_frame, textvariable=self.preset_var, width=20)
        self.preset_dropdown.pack(side=tk.LEFT, padx=5)
        self.preset_dropdown.bind("<<ComboboxSelected>>", self.load_preset)
        
        # Update the presets list
        self.update_preset_list()
        
        # Format hint
        time_hint = "Format: HH:MM (24-hour)" if self.time_format.get() == '24-hour' else "Format: HH:MM (12-hour)"
        self.format_hint = tk.Label(times_content, text=time_hint, bg='white', 
                                   fg=self.colors["text"], font=(self.font_family, 9, "italic"))
        self.format_hint.pack(pady=2)
        
        # Button Frame
        button_frame = tk.Frame(self.main_frame, bg=self.colors["background"])
        button_frame.pack(pady=15)
        
        # Custom button styling
        self.start_button = tk.Button(
            button_frame, 
            text="Start Reminders", 
            command=self.toggle_reminders,
            bg=self.colors["primary"], 
            fg="white", 
            width=15, 
            height=2,
            font=(self.font_family, 10, "bold"),
            relief=tk.RAISED,
            bd=1
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        test_button = tk.Button(
            button_frame, 
            text="Test Notification", 
            command=self.test_notification,
            bg=self.colors["primary"], 
            fg="white", 
            width=15, 
            height=2,
            font=(self.font_family, 10, "bold"),
            relief=tk.RAISED,
            bd=1
        )
        test_button.pack(side=tk.LEFT, padx=5)
        
        # Counter Frame - with animated counter
        counter_frame = tk.Frame(self.main_frame, bg='white', relief=tk.RIDGE, bd=1)
        counter_frame.pack(fill="x", padx=10, pady=10)
        
        # Add a subtle header
        counter_header = tk.Frame(counter_frame, bg=self.colors["primary"], height=8)
        counter_header.pack(fill="x")
        
        counter_title = tk.Label(counter_frame, text="Statistics", font=(self.font_family, 12, "bold"), 
                                bg='white', fg=self.colors["primary"])
        counter_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        # Inner content
        counter_content = tk.Frame(counter_frame, bg='white', padx=15, pady=10)
        counter_content.pack(fill="x")
        
        counter_label = tk.Label(counter_content, text="Reminder Days:", bg='white', 
                                font=(self.font_family, 10, "bold"))
        counter_label.pack(pady=5)
        
        # Canvas for animated counter
        self.counter_canvas = tk.Canvas(counter_content, width=100, height=60, 
                                       bg='white', highlightthickness=0)
        self.counter_canvas.pack(pady=5)
        
        # Draw the counter value
        self.count_display = self.counter_canvas.create_text(
            50, 30, text=str(self.reminder_count), 
            font=(self.font_family, 28, "bold"), fill=self.colors["primary"]
        )
        
        # Current time display with selected timezone
        time_frame = tk.Frame(self.main_frame, bg='white', relief=tk.RIDGE, bd=1)
        time_frame.pack(fill="x", padx=10, pady=10)
        
        # Add a subtle header
        time_header = tk.Frame(time_frame, bg=self.colors["primary"], height=8)
        time_header.pack(fill="x")
        
        # Inner content
        time_content = tk.Frame(time_frame, bg='white', padx=15, pady=10)
        time_content.pack(fill="x")
        
        tk.Label(time_content, text="Current Time:", bg='white', 
                font=(self.font_family, 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.time_display = tk.Label(time_content, text="", bg='white', 
                                    font=(self.font_family, 12, "bold"), fg=self.colors["primary"])
        self.time_display.pack(side=tk.LEFT, padx=5)
        
        # Start time display updating
        self.update_time_display()
        
        # Status Label
        self.status_frame = tk.Frame(self.main_frame, bg=self.colors["background"])
        self.status_frame.pack(pady=10)
        
        self.status_label = tk.Label(self.status_frame, text="Ready to start", 
                                    bg=self.colors["background"], fg=self.colors["text"], 
                                    font=(self.font_family, 10, "italic"))
        self.status_label.pack(pady=5)
        
        # Update button text based on current state
        if self.is_running:
            self.start_button.config(text="Stop Reminders")
            self.status_label.config(text="Reminders are active")

    def on_button_hover(self, event, button):
        """Darken button on hover"""
        # Convert hex to RGB
        r = int(self.colors["primary"][1:3], 16)
        g = int(self.colors["primary"][3:5], 16)
        b = int(self.colors["primary"][5:7], 16)
        
        # Darken by 20%
        r = max(0, int(r * 0.8))
        g = max(0, int(g * 0.8))
        b = max(0, int(b * 0.8))
        
        # Convert back to hex
        darker_color = f"#{r:02x}{g:02x}{b:02x}"
        button.config(bg=darker_color)

    def on_button_leave(self, event, button):
        """Restore button color on leave"""
        button.config(bg=self.colors["primary"])

    def save_preset(self):
        """Save current time settings as a preset"""
        import tkinter.simpledialog
        
        # Ask for preset name
        preset_name = tk.simpledialog.askstring("Save Preset", "Enter a name for this preset:")
        if preset_name:
            # Get current time settings
            preset_data = {
                "clock_in_time": self.clock_in_time.get(),
                "clock_out_time": self.clock_out_time.get(),
                "time_format": self.time_format.get()
            }
            
            # Add AM/PM settings if in 12-hour mode
            if self.time_format.get() == '12-hour' and hasattr(self, 'clock_in_ampm'):
                preset_data["clock_in_ampm"] = self.clock_in_ampm.get()
                preset_data["clock_out_ampm"] = self.clock_out_ampm.get()
            
            # Load existing presets
            presets = self.load_presets()
            
            # Add or update preset
            presets[preset_name] = preset_data
            
            # Save presets
            try:
                preset_file = self.data_dir / "clock_reminder_presets.json"
                with open(preset_file, "w") as f:
                    json.dump(presets, f)
                
                # Update presets dropdown
                self.update_preset_list()
                
                messagebox.showinfo("Success", f"Preset '{preset_name}' saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save preset: {str(e)}")
    
    def update_time_display(self):
        """Update the current time display with selected timezone"""
        try:
            # Get the current time in the selected timezone
            if self.timezone.get() == 'Local' or not pytz:
                now = datetime.datetime.now()
            else:
                # Use pytz to get the time in the selected timezone
                try:
                    tz = pytz.timezone(self.timezone.get())
                    now = datetime.datetime.now(tz)
                except:
                    # Fallback to local time if timezone is invalid
                    now = datetime.datetime.now()
                    
            # Format the time according to the selected time format
            if self.time_format.get() == '12-hour':
                time_str = now.strftime("%I:%M:%S %p")
            else:
                time_str = now.strftime("%H:%M:%S")
                
            # Add the timezone name
            if self.timezone.get() != 'Local' and pytz:
                time_str += f" ({self.timezone.get()})"
                
            # Update the label
            self.time_display.config(text=time_str)
        except Exception as e:
            print(f"Error updating time display: {e}")
            
        # Schedule the next update (every second)
        self.root.after(1000, self.update_time_display)

    def toggle_reminders(self):
        if not self.is_running:
            # Validate time format
            try:
                self.validate_time_format(self.clock_in_time.get())
                self.validate_time_format(self.clock_out_time.get())
                self.start_reminders()
                
                # Update button appearance
                self.start_button.config(text="Stop Reminders")
                
                # Update status
                self.status_label.config(text="Reminders are active", fg=self.colors["primary"])
            except ValueError as e:
                messagebox.showerror("Invalid Time Format", str(e))
        else:
            self.stop_reminders()
            
            # Update button appearance
            self.start_button.config(text="Start Reminders")
            
            # Update status
            self.status_label.config(text="Reminders stopped", fg=self.colors["text"])

    def validate_time_format(self, time_str):
        """Validate the time format based on current settings"""
        try:
            if self.time_format.get() == '24-hour':
                # 24-hour format validation
                hours, minutes = map(int, time_str.split(':'))
                if not (0 <= hours < 24 and 0 <= minutes < 60):
                    raise ValueError
            else:
                # 12-hour format validation
                hours, minutes = map(int, time_str.split(':'))
                if not (1 <= hours <= 12 and 0 <= minutes < 60):
                    raise ValueError
        except:
            raise ValueError(f"Please enter a valid time in {self.time_format.get()} format")

    def get_24h_time(self, time_str, am_pm=None):
        """Convert time to 24-hour format for internal processing"""
        if self.time_format.get() == '24-hour':
            return time_str
        else:
            # Convert from 12-hour to 24-hour
            hours, minutes = map(int, time_str.split(':'))
            # Get AM/PM from the appropriate combobox
            if am_pm == 'clock_in':
                period = self.clock_in_ampm.get()
            elif am_pm == 'clock_out':
                period = self.clock_out_ampm.get()
            else:
                period = 'AM'  # Default
                
            if period == 'PM' and hours < 12:
                hours += 12
            elif period == 'AM' and hours == 12:
                hours = 0
                
            return f"{hours:02d}:{minutes:02d}"

    def start_reminders(self):
        self.is_running = True
        self.save_data()
        
        # Create and start reminder thread
        self.reminder_thread = threading.Thread(target=self.reminder_loop, daemon=True)
        self.reminder_thread.start()

    def stop_reminders(self):
        self.is_running = False
        self.save_data()

    def reminder_loop(self):
        last_date = None
        
        while self.is_running:
            # Get current time in the selected timezone
            if self.timezone.get() == 'Local' or not pytz:
                now = datetime.datetime.now()
            else:
                try:
                    tz = pytz.timezone(self.timezone.get())
                    now = datetime.datetime.now(tz)
                except:
                    # Fallback to local time if timezone is invalid
                    now = datetime.datetime.now()
            
            current_time = now.strftime("%H:%M")  # Always use 24h format for comparison
            current_date = now.strftime("%Y-%m-%d")
            
            # Convert input times to 24h format for comparison
            clock_in_24h = self.get_24h_time(self.clock_in_time.get(), 'clock_in')
            clock_out_24h = self.get_24h_time(self.clock_out_time.get(), 'clock_out')
            
            # Check if we need to send clock-in reminder
            if current_time == clock_in_24h:
                self.show_notification(
                    "Clock In Reminder",
                    f"It's time to clock in! ({current_time})"
                )
                
                # If this is a new day, increment counter
                if last_date != current_date:
                    last_date = current_date
                    self.reminder_count += 1
                    # Use after() to safely update UI from another thread
                    self.root.after(0, self.update_counter)
            
            # Check if we need to send clock-out reminder
            if current_time == clock_out_24h:
                self.show_notification(
                    "Clock Out Reminder",
                    f"It's time to clock out! ({current_time})"
                )
            
            # Save data periodically
            self.save_data()
            
            # Check every minute
            time.sleep(60 - datetime.datetime.now().second)

    def update_counter(self):
        """Update counter with animation"""
        self.animate_counter(self.reminder_count)
        self.save_data()

    def show_notification(self, title, message):
        """Display a notification using the macOS notification system"""
        try:
            # For macOS, use osascript to show notification
            notification_script = f'''
            display notification "{message}" with title "{title}"
            '''
            os.system(f"osascript -e '{notification_script}'")
            
            # Also highlight the dinosaur
            self.highlight_dino()
            
        except Exception as e:
            print(f"Error showing notification: {e}")
            # Fallback to tkinter messagebox
            messagebox.showinfo(title, message)

    def highlight_dino(self):
        """Briefly highlight the dinosaur when notification is sent"""
        # Save original position and speed up animation
        orig_speed = self.dino_direction
        self.dino_direction = orig_speed * 3
        
        # Function to restore normal speed
        def restore_speed():
            self.dino_direction = orig_speed
        
        # Restore speed after 2 seconds
        self.root.after(2000, restore_speed)

    def test_notification(self):
        try:
            self.show_notification(
                "Test Notification",
                "This is a test reminder notification!"
            )
            
            # Show a success message
            messagebox.showinfo("Test", "Test notification sent!")
        except Exception as e:
            messagebox.showerror("Error", f"Could not send notification: {str(e)}")

    def save_data(self):
        """Save application data to JSON file"""
        data = {
            "clock_in_time": self.clock_in_time.get(),
            "clock_out_time": self.clock_out_time.get(),
            "reminder_count": self.reminder_count,
            "is_running": self.is_running,
            "time_format": self.time_format.get(),
            "timezone": self.timezone.get()
        }
        
        # Save AM/PM settings if in 12-hour mode
        if self.time_format.get() == '12-hour' and hasattr(self, 'clock_in_ampm'):
            data["clock_in_ampm"] = self.clock_in_ampm.get()
            data["clock_out_ampm"] = self.clock_out_ampm.get()
        
        try:
            data_file = self.data_dir / "clock_reminder_data.json"
            with open(data_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving data: {str(e)}")

    def load_data(self):
        """Load application data from JSON file"""
        try:
            data_file = self.data_dir / "clock_reminder_data.json"
            if data_file.exists():
                with open(data_file, "r") as f:
                    data = json.load(f)
                    self.clock_in_time.set(data.get("clock_in_time", "09:00"))
                    self.clock_out_time.set(data.get("clock_out_time", "17:00"))
                    self.reminder_count = data.get("reminder_count", 0)
                    self.is_running = data.get("is_running", False)
                    
                    # Load time format and timezone settings if available
                    if "time_format" in data:
                        self.time_format.set(data["time_format"])
                    if "timezone" in data:
                        self.timezone.set(data["timezone"])
                        
                    # Store AM/PM settings to be applied after widgets are created
                    self.saved_clock_in_ampm = data.get("clock_in_ampm", "AM")
                    self.saved_clock_out_ampm = data.get("clock_out_ampm", "PM")
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            
    def load_presets(self):
        """Load saved presets from file"""
        try:
            preset_file = self.data_dir / "clock_reminder_presets.json"
            if preset_file.exists():
                with open(preset_file, "r") as f:
                    return json.load(f)
        except:
            pass
        
        return {}  # Return empty dict if no presets or error

    def update_preset_list(self):
        """Update the presets dropdown with available presets"""
        presets = self.load_presets()
        
        # Update dropdown values
        self.preset_dropdown['values'] = list(presets.keys())
        
        # Select first item if available
        if self.preset_dropdown['values']:
            self.preset_dropdown.current(0)

    def load_preset(self, event=None):
        """Load selected preset"""
        preset_name = self.preset_var.get()
        if not preset_name:
            return
        
        # Load presets
        presets = self.load_presets()
        
        # Check if selected preset exists
        if preset_name in presets:
            preset_data = presets[preset_name]
            
            # Apply preset settings
            self.clock_in_time.set(preset_data.get("clock_in_time", "09:00"))
            self.clock_out_time.set(preset_data.get("clock_out_time", "17:00"))
            
            # Apply time format if different
            if preset_data.get("time_format") != self.time_format.get():
                self.time_format.set(preset_data.get("time_format", "24-hour"))
                self.update_time_format()
            
            # Apply AM/PM settings if in 12-hour mode
            if self.time_format.get() == '12-hour' and hasattr(self, 'clock_in_ampm'):
                if "clock_in_ampm" in preset_data:
                    self.clock_in_ampm.set(preset_data["clock_in_ampm"])
                if "clock_out_ampm" in preset_data:
                    self.clock_out_ampm.set(preset_data["clock_out_ampm"])
            
            messagebox.showinfo("Success", f"Loaded preset '{preset_name}'")
            
    def update_time_format(self, event=None):
        """Handle changes in the time format selection."""
        selected_format = self.time_format.get()

        # Update the hint label
        if selected_format == '24-hour':
            self.format_hint.config(text="Format: HH:MM (24-hour)")
            # Hide AM/PM selectors if they exist and are packed
            if hasattr(self, 'clock_in_ampm') and self.clock_in_ampm.winfo_ismapped():
                self.clock_in_ampm.pack_forget()
            if hasattr(self, 'clock_out_ampm') and self.clock_out_ampm.winfo_ismapped():
                self.clock_out_ampm.pack_forget()
        else: # 12-hour format
            self.format_hint.config(text="Format: HH:MM (12-hour)")
            # Show AM/PM selectors if they exist and are not already packed
            # Ensure they are placed correctly relative to the entry widget
            if hasattr(self, 'clock_in_ampm') and not self.clock_in_ampm.winfo_ismapped():
                self.clock_in_ampm.pack(side=tk.LEFT, padx=5, after=self.clock_in_entry)
            if hasattr(self, 'clock_out_ampm') and not self.clock_out_ampm.winfo_ismapped():
                self.clock_out_ampm.pack(side=tk.LEFT, padx=5, after=self.clock_out_entry)
        self.save_data() # Save the new format setting
        
    def start_animations(self):
        """Start the UI animations."""
        self.animation_active = True
        # Start dinosaur animation loop
        self.animate_dinosaur()
        # Initialize counter display (animation happens on update)
        self.update_counter_display(self.reminder_count) # Initial display

    def animate_dinosaur(self):
        """Animates the dinosaur walking back and forth."""
        if not self.animation_active:
            return # Stop animation if not active

        # Update position based on direction
        self.dino_position += self.dino_direction

        # Bounce off edges (adjust boundaries as needed for canvas width and dino size)
        # Assuming canvas width 100 and dino approx 8 pixels wide * 4 pixel_size = 32
        max_pos = 100 - (8 * 4) # Roughly 68
        if self.dino_position >= max_pos or self.dino_position <= 0:
            self.dino_direction *= -1 # Reverse direction

        # Redraw the dinosaur
        self.draw_dinosaur()

        # Schedule the next frame (adjust timing for speed, e.g., 100ms)
        self.root.after(100, self.animate_dinosaur)

    def animate_counter(self, target_value):
        """Animates the counter value increasing."""
        # Get current displayed value (handle potential errors)
        try:
            current_value_str = self.counter_canvas.itemcget(self.count_display, 'text')
            current_value = int(current_value_str)
        except:
             current_value = 0 # Default if text is not an int

        # Calculate step (can be adjusted for smoother/faster animation)
        step = math.ceil((target_value - current_value) / 10) # Move 1/10th of the way
        if step == 0 and target_value > current_value:
             step = 1 # Ensure at least 1 step increment if not yet at target

        next_value = current_value + step

        if next_value >= target_value:
            # Reached or passed target, set final value
            self.update_counter_display(target_value)
        else:
            # Update display and schedule next step
            self.update_counter_display(next_value)
            self.root.after(50, lambda: self.animate_counter(target_value)) # Adjust speed (50ms)

    def update_counter_display(self, value):
         """Helper function to update the counter canvas text."""
         self.counter_canvas.itemconfig(self.count_display, text=str(value))
    def show_notification(self, title, message):
        """Use multiple methods to ensure notification is shown"""
        # Print to console for confirmation
        print(f"\nNOTIFICATION: {title} - {message}\n")
        
        # Try multiple notification methods
        try:
            # Method 1: Terminal-based notification
            os.system(f"echo '\a'")  # Terminal bell
            
            # Method 2: Basic AppleScript
            os.system(f'''osascript -e 'tell application "System Events" to display dialog "{message}" with title "{title}" buttons {{"OK"}} default button 1' &''')
            
            # Highlight the dinosaur animation
            self.highlight_dino()
            
        except Exception as e:
            print(f"Error showing notification: {e}")
            # Fallback to tkinter messagebox
            self.root.after(0, lambda: messagebox.showinfo(title, message))


def main():
    # Create the main application window
    root = tk.Tk()

    # Create an instance of the ClockReminderApp
    app = ClockReminderApp(root)

    # Start the Tkinter event loop
    root.mainloop()


if __name__ == "__main__":
    main()