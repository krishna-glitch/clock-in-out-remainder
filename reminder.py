import tkinter as tk
from tkinter import messagebox, ttk
import time
import datetime
import json
import os
from threading import Thread
import sys
import pystray
from PIL import Image, ImageDraw
import pytz
import math
import random

class ClockReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Clock In/Out Reminder")
        self.root.geometry("500x550")
        self.root.resizable(False, False)
        
        # Set app icon and styling
        self.root.iconbitmap("clock.ico") if os.path.exists("clock.ico") else None
        
        # Add custom colors - Dark green & light gray theme
        self.colors = {
            "primary": "#31473A",    # Dark green
            "secondary": "#31473A",  # Dark green
            "success": "#31473A",    # Dark green
            "danger": "#31473A",     # Dark green
            "warning": "#31473A",    # Dark green
            "background": "#EDF4F2", # Light gray
            "text": "#31473A",       # Dark green
            "light_text": "#31473A"  # Dark green
        }
        
        self.root.configure(bg=self.colors["background"])
        
        # Configure ttk styles for better appearance
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 10, "bold"))
        self.style.configure("TCombobox", font=("Arial", 10))
        
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
        self.dino_direction = 1  # 1 for right, -1 for left
        
        # Load saved data
        self.load_data()
        
        # Create gradient background
        self.create_background()
        
        # Create GUI elements
        self.create_widgets()
        
        # Start dinosaur animation
        self.start_animations()
        
        # Check if app was started with "--minimized" argument for background startup
        if len(sys.argv) > 1 and sys.argv[1] == "--minimized":
            # Start minimized to system tray
            self.root.withdraw()
            self.create_system_tray()
            
        # Start reminder thread if app was previously running
        if self.is_running:
            self.start_reminders()

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
                              font=("Arial", 18, "bold"), bg=self.colors["background"], 
                              fg=self.colors["primary"])
        title_label.pack(pady=(0, 15))
        
        # Create card-like container for settings
        settings_frame = tk.Frame(self.main_frame, bg='white', 
                                 relief=tk.RIDGE, bd=1)
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        # Add a subtle header
        settings_header = tk.Frame(settings_frame, bg=self.colors["primary"], height=8)
        settings_header.pack(fill="x")
        
        settings_title = tk.Label(settings_frame, text="Settings", font=("Arial", 12, "bold"), 
                                 bg='white', fg=self.colors["primary"])
        settings_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        # Inner padding frame
        settings_content = tk.Frame(settings_frame, bg='white', padx=15, pady=10)
        settings_content.pack(fill="x")
        
        # Time Format Settings
        format_frame = tk.Frame(settings_content, bg='white')
        format_frame.pack(fill="x", pady=5)
        
        tk.Label(format_frame, text="Time Format:", font=("Arial", 10, "bold"), 
                bg='white').pack(side=tk.LEFT, padx=5)
        
        format_options = ttk.Combobox(format_frame, textvariable=self.time_format, width=10)
        format_options['values'] = ('12-hour', '24-hour')
        format_options.pack(side=tk.LEFT, padx=5)
        format_options.bind("<<ComboboxSelected>>", self.update_time_format)
        
        # Timezone Settings
        timezone_frame = tk.Frame(settings_content, bg='white')
        timezone_frame.pack(fill="x", pady=5)
        
        tk.Label(timezone_frame, text="Time Zone:", font=("Arial", 10, "bold"), 
                bg='white').pack(side=tk.LEFT, padx=5)
        
        timezone_options = ttk.Combobox(timezone_frame, textvariable=self.timezone, width=25)
        popular_timezones = ['Local', 'US/Eastern', 'US/Central', 'US/Mountain', 'US/Pacific', 
                           'Europe/London', 'Europe/Paris', 'Asia/Tokyo', 'Australia/Sydney']
        timezone_options['values'] = popular_timezones
        timezone_options.pack(side=tk.LEFT, padx=5)
        
        # Create card-like container for time inputs
        times_frame = tk.Frame(self.main_frame, bg='white', 
                              relief=tk.RIDGE, bd=1)
        times_frame.pack(fill="x", padx=10, pady=10)
        
        # Add a subtle header
        times_header = tk.Frame(times_frame, bg=self.colors["primary"], height=8)
        times_header.pack(fill="x")
        
        times_title = tk.Label(times_frame, text="Reminder Times", font=("Arial", 12, "bold"), 
                              bg='white', fg=self.colors["primary"])
        times_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        # Inner padding frame
        times_content = tk.Frame(times_frame, bg='white', padx=15, pady=10)
        times_content.pack(fill="x")
        
        # Clock In Frame
        clock_in_frame = tk.Frame(times_content, bg='white')
        clock_in_frame.pack(fill="x", pady=5)
        
        clock_in_label = tk.Label(clock_in_frame, text="Clock In Time:", font=("Arial", 10, "bold"), 
                                 bg='white')
        clock_in_label.pack(side=tk.LEFT, padx=5)
        
        self.clock_in_entry = tk.Entry(clock_in_frame, textvariable=self.clock_in_time, width=10,
                                      font=("Arial", 10), justify="center",
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
        
        clock_out_label = tk.Label(clock_out_frame, text="Clock Out Time:", font=("Arial", 10, "bold"), 
                                  bg='white')
        clock_out_label.pack(side=tk.LEFT, padx=5)
        
        self.clock_out_entry = tk.Entry(clock_out_frame, textvariable=self.clock_out_time, width=10,
                                       font=("Arial", 10), justify="center",
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
            font=("Arial", 9),
            relief=tk.RAISED,
            bd=1
        )
        save_button.pack(pady=5)
        
        # Load presets dropdown
        preset_frame = tk.Frame(times_content, bg='white')
        preset_frame.pack(fill="x", pady=5)
        
        tk.Label(preset_frame, text="Load Preset:", font=("Arial", 10, "bold"), 
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
                                   fg=self.colors["text"], font=("Arial", 9, "italic"))
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
            font=("Arial", 10, "bold"),
            relief=tk.RAISED,
            bd=1,
            activebackground=self.colors["primary"],
            activeforeground="white"
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
            font=("Arial", 10, "bold"),
            relief=tk.RAISED,
            bd=1,
            activebackground=self.colors["primary"],
            activeforeground="white"
        )
        test_button.pack(side=tk.LEFT, padx=5)
        
        # Add hover effects to buttons
        self.start_button.bind("<Enter>", lambda e: self.on_button_hover(e, self.start_button))
        self.start_button.bind("<Leave>", lambda e: self.on_button_leave(e, self.start_button))
        test_button.bind("<Enter>", lambda e: self.on_button_hover(e, test_button))
        test_button.bind("<Leave>", lambda e: self.on_button_leave(e, test_button))
        save_button.bind("<Enter>", lambda e: self.on_button_hover(e, save_button))
        save_button.bind("<Leave>", lambda e: self.on_button_leave(e, save_button))
        
        # Counter Frame - with animated counter
        counter_frame = tk.Frame(self.main_frame, bg='white', relief=tk.RIDGE, bd=1)
        counter_frame.pack(fill="x", padx=10, pady=10)
        
        # Add a subtle header
        counter_header = tk.Frame(counter_frame, bg=self.colors["primary"], height=8)
        counter_header.pack(fill="x")
        
        counter_title = tk.Label(counter_frame, text="Statistics", font=("Arial", 12, "bold"), 
                                bg='white', fg=self.colors["primary"])
        counter_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        # Inner content
        counter_content = tk.Frame(counter_frame, bg='white', padx=15, pady=10)
        counter_content.pack(fill="x")
        
        counter_label = tk.Label(counter_content, text="Reminder Days:", bg='white', 
                                font=("Arial", 10, "bold"))
        counter_label.pack(pady=5)
        
        # Canvas for animated counter
        self.counter_canvas = tk.Canvas(counter_content, width=100, height=60, 
                                       bg='white', highlightthickness=0)
        self.counter_canvas.pack(pady=5)
        
        # Draw the counter value
        self.count_display = self.counter_canvas.create_text(
            50, 30, text=str(self.reminder_count), 
            font=("Arial", 28, "bold"), fill=self.colors["primary"]
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
                font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.time_display = tk.Label(time_content, text="", bg='white', 
                                    font=("Arial", 12, "bold"), fg=self.colors["primary"])
        self.time_display.pack(side=tk.LEFT, padx=5)
        
        # Start time display updating
        self.update_time_display()
        
        # Status Label with fade-in animation
        self.status_frame = tk.Frame(self.main_frame, bg=self.colors["background"])
        self.status_frame.pack(pady=10)
        
        self.status_label = tk.Label(self.status_frame, text="Ready to start", 
                                    bg=self.colors["background"], fg=self.colors["text"], 
                                    font=("Arial", 10, "italic"))
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
        # Add dependency for dialog boxes
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
                with open("clock_reminder_presets.json", "w") as f:
                    json.dump(presets, f)
                
                # Update presets dropdown
                self.update_preset_list()
                
                messagebox.showinfo("Success", f"Preset '{preset_name}' saved successfully!")
            except Exception as e:
                self.time_display.config(text="Error: " + str(e))
    
    def update_time_display(self):
        """Update the current time display with selected timezone"""
        try:
            # Get the current time in the selected timezone
            if self.timezone.get() == 'Local':
                now = datetime.datetime.now()
            else:
                # Use pytz to get the time in the selected timezone
                tz = pytz.timezone(self.timezone.get())
                now = datetime.datetime.now(tz)
            
            # Format the time according to the selected time format
            if self.time_format.get() == '12-hour':
                time_str = now.strftime("%I:%M:%S %p")
            else:
                time_str = now.strftime("%H:%M:%S")
                
            # Add the timezone name
            if self.timezone.get() != 'Local':
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
        self.reminder_thread = Thread(target=self.reminder_loop, daemon=True)
        self.reminder_thread.start()

    def stop_reminders(self):
        self.is_running = False
        self.save_data()

    def reminder_loop(self):
        last_date = None
        
        while self.is_running:
            # Get current time in the selected timezone
            if self.timezone.get() == 'Local':
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
        """Display a notification using tkinter or the system tray"""
        try:
            # Try using the system tray for notification
            if hasattr(self, 'tray_icon'):
                self.tray_icon.notify(title, message)
                
                # Add highlight animation to the dinosaur
                self.highlight_dino()
            else:
                # Fallback to a tkinter popup if tray icon not available
                if not self.root.winfo_viewable():
                    # If window is hidden, briefly show it
                    self.root.deiconify()
                    self.root.attributes('-topmost', True)
                    messagebox.showinfo(title, message)
                    self.root.attributes('-topmost', False)
                    self.root.withdraw()
                else:
                    messagebox.showinfo(title, message)
        except Exception as e:
            print(f"Error showing notification: {str(e)}")

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

    def create_system_tray(self):
        """Create system tray icon and menu"""
        # Create a simple icon
        icon_image = self.create_tray_icon()
        
        menu = (
            pystray.MenuItem('Show', self.show_window),
            pystray.MenuItem('Start/Stop Reminders', self.toggle_reminders_tray),
            pystray.MenuItem('Exit', self.exit_app)
        )
        
        self.tray_icon = pystray.Icon("ClockReminder")
        self.tray_icon.icon = icon_image
        self.tray_icon.menu = pystray.Menu(*menu)
        self.tray_icon.title = "Clock In/Out Reminder"
        
        # Run the icon in a separate thread
        Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self):
        """Show the main window from system tray with animation"""
        # First make sure window is ready to show
        self.root.update()
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Get window dimensions
        window_width = 500
        window_height = 550
        
        # Calculate center position
        center_x = (screen_width - window_width) // 2
        center_y = (screen_height - window_height) // 2
        
        # Start position (off-screen)
        start_y = screen_height
        
        # Set initial position (off-screen)
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{start_y}")
        
        # Show window
        self.root.deiconify()
        
        # Animate window coming into view
        def animate_window(current_y):
            if current_y > center_y:
                # Move window up
                self.root.geometry(f"{window_width}x{window_height}+{center_x}+{current_y}")
                # Continue animation
                self.root.after(10, lambda: animate_window(current_y - 30))
            else:
                # Final position
                self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
                # Focus
                self.root.focus_force()
        
        # Start animation
        animate_window(start_y)

    def toggle_reminders_tray(self):
        """Toggle reminders from the system tray"""
        if self.is_running:
            self.stop_reminders()
            self.start_button.config(text="Start Reminders")
            self.status_label.config(text="Reminders stopped")
        else:
            try:
                self.validate_time_format(self.clock_in_time.get())
                self.validate_time_format(self.clock_out_time.get())
                self.start_reminders()
                self.start_button.config(text="Stop Reminders")
                self.status_label.config(text="Reminders are active")
            except ValueError as e:
                # Can't show messagebox when minimized, so just don't start
                print(f"Error starting reminders: {str(e)}")

    def create_tray_icon(self):
        """Create a simple dinosaur icon for the system tray"""
        # If the icon file exists, use it
        if os.path.exists("clock.ico"):
            return Image.open("clock.ico")
            
        # Otherwise create a simple icon
        width = 64
        height = 64
        
        # Convert hex to RGB
        color_rgb = (int(self.colors["primary"][1:3], 16), 
                    int(self.colors["primary"][3:5], 16), 
                    int(self.colors["primary"][5:7], 16))
        
        background_rgb = (int(self.colors["background"][1:3], 16), 
                         int(self.colors["background"][3:5], 16), 
                         int(self.colors["background"][5:7], 16))
        
        image = Image.new('RGB', (width, height), color=background_rgb)
        dc = ImageDraw.Draw(image)
        
        # Draw a simple pixelated dinosaur
        pixel_size = 4
        
        # Dinosaur pixel art (8x8 grid centered in the icon)
        dino_pixels = [
            (3, 3), (3, 4), (3, 5),
            (4, 2), (4, 3), (4, 4), (4, 5), (4, 6),
            (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7),
            (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6),
            (7, 2), (7, 3), (7, 4), (7, 5),
            (4, 7), (6, 7)  # Legs
        ]
        
        # Draw dinosaur pixel by pixel
        for px, py in dino_pixels:
            dc.rectangle(
                (px * pixel_size, py * pixel_size, 
                 (px + 1) * pixel_size, (py + 1) * pixel_size),
                fill=color_rgb
            )
        
        # Draw eye (white pixel)
        dc.rectangle(
            (5 * pixel_size, 2 * pixel_size, 
             6 * pixel_size, 3 * pixel_size),
            fill=(255, 255, 255)
        )
        
        return image
        
    def exit_app(self):
        """Exit the application from system tray with fade-out effect"""
        # Save data first
        self.save_data()
        
        # If window is visible, create fade-out effect
        if self.root.winfo_viewable():
            self.fade_out_window()
        else:
            # Just close everything
            if hasattr(self, 'tray_icon'):
                self.tray_icon.stop()
            self.root.destroy()
            sys.exit(0)

    def fade_out_window(self, alpha=1.0):
        """Create a fade-out effect when closing the app"""
        if alpha > 0:
            # Set window transparency (if supported)
            try:
                self.root.attributes('-alpha', alpha)
                # Continue fading
                self.root.after(50, lambda: self.fade_out_window(alpha - 0.1))
            except:
                # Transparency not supported, just close
                if hasattr(self, 'tray_icon'):
                    self.tray_icon.stop()
                self.root.destroy()
                sys.exit(0)
        else:
            # Completely faded out, close app
            if hasattr(self, 'tray_icon'):
                self.tray_icon.stop()
            self.root.destroy()
            sys.exit(0)

    def minimize_to_tray(self):
        """Minimize the application to system tray"""
        # Make sure system tray icon exists
        if not hasattr(self, 'tray_icon'):
            self.create_system_tray()
        
        # Hide the window
        self.root.withdraw()
        
        # Show notification
        self.show_notification(
            "App Minimized",
            "The app is still running in the system tray"
        )
        
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
            with open("clock_reminder_data.json", "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving data: {str(e)}")

    def load_data(self):
        """Load application data from JSON file"""
        try:
            if os.path.exists("clock_reminder_data.json"):
                with open("clock_reminder_data.json", "r") as f:
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
            if os.path.exists("clock_reminder_presets.json"):
                with open("clock_reminder_presets.json", "r") as f:
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