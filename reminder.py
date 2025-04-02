#!/usr/bin/env python3
# Clock In/Out Reminder
# A cross-platform desktop app that reminds you when to clock in and out

import tkinter as tk
from tkinter import messagebox, ttk
import time
import datetime
import json
import os
import sys
import threading
from pathlib import Path
import platform
import math
import random
import subprocess

# Platform detection
PLATFORM = platform.system().lower()  # 'windows', 'darwin' (macOS), or 'linux'

# ========================================================================================
# DEPENDENCY CHECKING
# ========================================================================================
def check_dependencies():
    """Check if required dependencies are installed and prompt for installation if needed"""
    missing_deps = []
    
    # Try importing optional dependencies
    try:
        import pytz
        print("pytz is installed")
    except ImportError:
        missing_deps.append("pytz")
        print("pytz is not installed - timezone functionality will be limited")
        
    try:
        from PIL import Image, ImageDraw
        print("Pillow is installed")
    except ImportError:
        missing_deps.append("pillow")
        print("Pillow is not installed - icon creation will be limited")
    
    # Platform-specific dependencies
    if PLATFORM == 'windows':
        try:
            import pystray
            print("pystray is installed")
        except ImportError:
            missing_deps.append("pystray")
            print("pystray is not installed - system tray functionality will be limited")
            
        try:
            from win10toast import ToastNotifier
            print("win10toast is installed")
        except ImportError:
            missing_deps.append("win10toast")
            print("win10toast is not installed - notification functionality will be limited")
    
    # If there are missing dependencies, offer to install them
    if missing_deps and messagebox.askyesno(
        "Missing Dependencies", 
        f"The following dependencies are missing: {', '.join(missing_deps)}\n\n"
        "Would you like to install them now? This may take a moment."
    ):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_deps)
            messagebox.showinfo("Success", "Dependencies installed successfully. Please restart the application.")
            sys.exit(0)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install dependencies: {str(e)}")

# Delayed imports to handle missing dependencies gracefully
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False

# Platform-specific imports
if PLATFORM == 'windows':
    try:
        from win10toast import ToastNotifier
        TOAST_AVAILABLE = True
    except ImportError:
        TOAST_AVAILABLE = False

    try:
        import winsound
        WINSOUND_AVAILABLE = True
    except ImportError:
        WINSOUND_AVAILABLE = False
        
    try:
        import pystray
        TRAY_SUPPORT = True
    except ImportError:
        TRAY_SUPPORT = False
elif PLATFORM == 'darwin':
    # For macOS, we'll use native osascript for notifications
    TOAST_AVAILABLE = False
    WINSOUND_AVAILABLE = False
    TRAY_SUPPORT = False
else:
    # For Linux, try to use notify-send for notifications
    TOAST_AVAILABLE = False
    WINSOUND_AVAILABLE = False
    try:
        import pystray
        TRAY_SUPPORT = True
    except ImportError:
        TRAY_SUPPORT = False

# ========================================================================================
# ICON CREATION
# ========================================================================================
def create_app_icon(save_path):
    """Create a default app icon and save it to the specified path"""
    if not PIL_AVAILABLE:
        print("Cannot create icon: PIL not available")
        return None
        
    try:
        # Create a simple clock icon
        width, height = 64, 64
        image = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a circle for the clock face (light gray)
        draw.ellipse((5, 5, width-5, height-5), fill=(237, 244, 242, 255), outline=(49, 71, 58, 255), width=2)
        
        # Draw clock hands
        center_x, center_y = width // 2, height // 2
        
        # Hour hand (shorter)
        hour_hand_length = 15
        draw.line(
            (center_x, center_y, center_x, center_y - hour_hand_length), 
            fill=(49, 71, 58, 255), 
            width=3
        )
        
        # Minute hand (longer)
        minute_hand_length = 25
        draw.line(
            (center_x, center_y, center_x + minute_hand_length // 2, center_y + minute_hand_length // 2), 
            fill=(49, 71, 58, 255), 
            width=2
        )
        
        # Draw center dot
        draw.ellipse((center_x-3, center_y-3, center_x+3, center_y+3), fill=(49, 71, 58, 255))
        
        # Save in the appropriate format based on platform
        if PLATFORM == 'windows':
            icon_path = Path(save_path) / "clock.ico"
            image.save(icon_path, format="ICO")
        else:
            icon_path = Path(save_path) / "clock.png"
            image.save(icon_path, format="PNG")
            
        print(f"Created application icon at {icon_path}")
        return str(icon_path)
    except Exception as e:
        print(f"Error creating icon: {e}")
        return None

# ========================================================================================
# NOTIFICATION SYSTEM
# ========================================================================================
def show_notification(title, message, root=None, icon_path=None):
    """Show a notification using the best available method for the platform"""
    notification_shown = False
    
    # Windows notifications
    if PLATFORM == 'windows':
        # Method 1: Try win10toast
        if TOAST_AVAILABLE:
            try:
                toaster = ToastNotifier()
                toaster.show_toast(
                    title, 
                    message, 
                    icon_path=icon_path if icon_path and os.path.exists(icon_path) else None,
                    duration=5,
                    threaded=True
                )
                notification_shown = True
                print(f"Notification via win10toast: {title} - {message}")
            except Exception as e:
                print(f"Error with win10toast notification: {e}")
        
        # Method 2: Use winsound for audio alert
        if WINSOUND_AVAILABLE and not notification_shown:
            try:
                winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
                print(f"\n[NOTIFICATION] {title}: {message}\n")
                notification_shown = True
            except Exception as e:
                print(f"Error playing notification sound: {e}")
    
    # macOS notifications
    elif PLATFORM == 'darwin':
        try:
            # Use osascript to show a notification
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(['osascript', '-e', script], check=True)
            notification_shown = True
            print(f"Notification via osascript: {title} - {message}")
        except Exception as e:
            print(f"Error with macOS notification: {e}")
    
    # Linux notifications
    elif PLATFORM == 'linux':
        try:
            # Try using notify-send command
            subprocess.call(['notify-send', title, message])
            notification_shown = True
            print(f"Notification via notify-send: {title} - {message}")
        except Exception as e:
            print(f"Error with Linux notification: {e}")
    
    # Custom notification window as fallback if we have a root window
    if not notification_shown and root is not None:
        try:
            notif_win = tk.Toplevel(root)
            notif_win.title(title)
            notif_win.geometry("300x100")
            notif_win.attributes('-topmost', True)
            notif_win.lift()           # Bring the window to the front
            notif_win.focus_force()    # Force the focus
            
            # Add message
            tk.Label(notif_win, text=message, pady=20, padx=20).pack(expand=True, fill='both')
            
            # Auto-close after 5 seconds
            notif_win.after(5000, notif_win.destroy)
            notification_shown = True
            print(f"Custom notification window shown: {title} - {message}")
        except Exception as e:
            print(f"Error with custom notification window: {e}")

    
    # Last resort - use messagebox if available
    if not notification_shown and root is not None:
        try:
            messagebox.showinfo(title, message)
            notification_shown = True
            print(f"Notification via messagebox: {title} - {message}")
        except Exception as e:
            print(f"Error with messagebox notification: {e}")
    
    # If all else fails, just print to console
    if not notification_shown:
        print(f"\n{'=' * 50}")
        print(f"NOTIFICATION: {title}")
        print(f"{message}")
        print(f"{'=' * 50}\n")
        notification_shown = True
    
    return notification_shown

# ========================================================================================
# MAIN APPLICATION
# ========================================================================================
class ClockReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Clock In/Out Reminder")
        self.root.geometry("500x400")
        #self.root.resizable(False, False)
        
        # Get app directory and create data directory
        self.app_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = self.get_data_dir()
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Set app icon
        self.set_app_icon()
        
        # Define colors - Dark green & light gray theme
        self.colors = {
            "primary": "#31473A",    # Dark green
            "secondary": "#31473A",  # Dark green
            "background": "#EDF4F2", # Light gray
            "text": "#31473A",       # Dark green
            "highlight": "#4CAF50",  # Brighter green for animations
            "warning": "#FFC107"     # Warning color
        }
        
        self.root.configure(bg=self.colors["background"])
        
        # Configure platform-specific fonts
        self.set_platform_fonts()
        
        # Initialize variables
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
        self.next_event_text = tk.StringVar(value="")
        
        # Animation variables for countdown
        self.countdown_progress = 0  # 0 to 100
        self.countdown_hours = 0
        self.countdown_minutes = 0
        self.countdown_seconds = 0
        
        # Load saved data
        self.load_data()
        
        # Create UI components
        self.create_scrollable_area()
        self.create_widgets()
        
        # Start animations
        self.start_animations()
        
        # Update time remaining display
        self.update_time_remaining()

        
        self.create_scrollable_area()
        self.scroll_canvas.bind("<Enter>", lambda e: self.scroll_canvas.focus_set())
        self.scroll_canvas.bind("<MouseWheel>", self._on_mousewheel)


        # Start reminder thread if app was previously running
        if self.is_running:
            self.start_reminders()
            
        # Set up close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    def _on_mousewheel(self, event):
        # event.delta is typically 120 or -120 per notch on Windows
        self.scroll_canvas.yview_scroll(int(-event.delta/120), "units")
        return "break"


    
    def get_data_dir(self):
        """Get platform-specific data directory for app files"""
        if PLATFORM == 'windows':
            # Windows: Use %APPDATA%\ClockReminder
            return Path(os.environ.get('APPDATA', str(Path.home()))) / "ClockReminder"
        elif PLATFORM == 'darwin':
            # macOS: Use ~/Library/Application Support/ClockReminder
            return Path.home() / "Library" / "Application Support" / "ClockReminder"
        else:
            # Linux/Others: Use ~/.clockreminder
            return Path.home() / ".clockreminder"
    
    def set_app_icon(self):
        """Set application icon or create a default one if none exists"""
        # Check for existing icon files
        icon_paths = [
            self.app_dir / "clock.ico",
            self.app_dir / "clock.png",
            self.app_dir / "clock.icns"
        ]
        
        icon_found = False
        for icon_path in icon_paths:
            if icon_path.exists():
                try:
                    if PLATFORM == 'windows' and icon_path.suffix == '.ico':
                        self.root.iconbitmap(str(icon_path))
                        self.icon_path = str(icon_path)
                        icon_found = True
                        break
                    elif hasattr(self.root, 'iconphoto'):
                        icon_img = tk.PhotoImage(file=str(icon_path))
                        self.root.iconphoto(True, icon_img)
                        self.icon_path = str(icon_path)
                        icon_found = True
                        break
                except Exception as e:
                    print(f"Error setting icon {icon_path}: {e}")
        
        # Create default icon if none found
        if not icon_found:
            icon_path = create_app_icon(self.app_dir)
            if icon_path:
                self.icon_path = icon_path
                try:
                    if PLATFORM == 'windows' and icon_path.endswith('.ico'):
                        self.root.iconbitmap(icon_path)
                    elif hasattr(self.root, 'iconphoto') and Path(icon_path).exists():
                        icon_img = tk.PhotoImage(file=icon_path)
                        self.root.iconphoto(True, icon_img)
                except Exception as e:
                    print(f"Error setting created icon: {e}")
            else:
                self.icon_path = None
    
    def set_platform_fonts(self):
        """Configure platform-specific fonts"""
        # Default font family based on platform
        if PLATFORM == 'windows':
            self.font_family = "Arial"
        elif PLATFORM == 'darwin':
            self.font_family = "SF Pro"  # macOS default font
        else:
            self.font_family = "DejaVu Sans"  # Common Linux font
            
        # Configure ttk styles for better appearance
        self.style = ttk.Style()
        self.style.configure("TButton", font=(self.font_family, 10, "bold"))
        self.style.configure("TCombobox", font=(self.font_family, 10))
    
    def create_background(self):
        """Create a background canvas for the application"""
        self.canvas = tk.Canvas(self.root, width=500, height=600, 
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
        if PYTZ_AVAILABLE:
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
            font=(self.font_family, 10, "bold"),
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
            font=(self.font_family, 28, "bold"), fill=self.colors["primary"])
        
        # Current time display with timezone
        time_frame = tk.Frame(self.main_frame, bg='white', relief=tk.RIDGE, bd=1)
        time_frame.pack(fill="x", padx=10, pady=10)
        
        # Add a subtle header
        time_header = tk.Frame(time_frame, bg=self.colors["primary"], height=8)
        time_header.pack(fill="x")
        
        time_title = tk.Label(time_frame, text="Current Time", font=(self.font_family, 12, "bold"), 
                             bg='white', fg=self.colors["primary"])
        time_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        # Inner content
        time_content = tk.Frame(time_frame, bg='white', padx=15, pady=10)
        time_content.pack(fill="x")
        
        self.time_display = tk.Label(time_content, text="", bg='white', 
                                    font=(self.font_family, 16, "bold"), fg=self.colors["primary"])
        self.time_display.pack(pady=5)
        
        # Start time display updating
        self.update_time_display()
        
        # Time until next event display with animation
        next_event_frame = tk.Frame(self.main_frame, bg='white', relief=tk.RIDGE, bd=1)
        next_event_frame.pack(fill="x", padx=10, pady=10)
        
        # Add a subtle header
        next_event_header = tk.Frame(next_event_frame, bg=self.colors["primary"], height=8)
        next_event_header.pack(fill="x")
        
        next_event_title = tk.Label(next_event_frame, text="Next Reminder", font=(self.font_family, 12, "bold"), 
                                   bg='white', fg=self.colors["primary"])
        next_event_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        # Inner content
        next_event_content = tk.Frame(next_event_frame, bg='white', padx=15, pady=10)
        next_event_content.pack(fill="x")
        
        # Text display for next event
        self.next_event_label = tk.Label(next_event_content, text="",
                                       bg='white', font=(self.font_family, 11, "bold"), 
                                       fg=self.colors["primary"])
        self.next_event_label.pack(pady=(5, 10))
        
        # Animated progress bar for countdown
        self.countdown_canvas = tk.Canvas(next_event_content, width=400, height=40, 
                                       bg='white', highlightthickness=0)
        self.countdown_canvas.pack(pady=5)
        
        # Draw the progress bar background
        self.progress_bg = self.countdown_canvas.create_rectangle(
            10, 10, 390, 30, fill="#E0E0E0", outline="")
        
        # Draw the progress bar
        self.progress_bar = self.countdown_canvas.create_rectangle(
            10, 10, 10, 30, fill=self.colors["primary"], outline="")
        
        # Draw the time remaining text
        self.countdown_text = self.countdown_canvas.create_text(
            200, 20, text="00:00:00", font=(self.font_family, 12, "bold"), 
            fill="black")
        
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
    
    # =========================
    # Missing Functionality Implementations
    # =========================
    def load_data(self):
        """Load saved settings from a JSON file if it exists."""
        settings_file = self.data_dir / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, "r") as f:
                    data = json.load(f)
                    self.clock_in_time.set(data.get("clock_in_time", "09:00"))
                    self.clock_out_time.set(data.get("clock_out_time", "17:00"))
                    self.reminder_count = data.get("reminder_count", 0)
                    self.time_format.set(data.get("time_format", "24-hour"))
                    self.timezone.set(data.get("timezone", "Local"))
                    self.is_running = data.get("is_running", False)
            except Exception as e:
                print(f"Error loading data: {e}")
    
    def save_data(self):
        """Save current settings to a JSON file."""
        settings_file = self.data_dir / "settings.json"
        data = {
            "clock_in_time": self.clock_in_time.get(),
            "clock_out_time": self.clock_out_time.get(),
            "reminder_count": self.reminder_count,
            "time_format": self.time_format.get(),
            "timezone": self.timezone.get(),
            "is_running": self.is_running
        }
        try:
            with open(settings_file, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def save_preset(self):
        """Save current times as a preset."""
        preset_name = "Preset " + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        preset = {
            "name": preset_name,
            "clock_in_time": self.clock_in_time.get(),
            "clock_out_time": self.clock_out_time.get()
        }
        presets_file = self.data_dir / "presets.json"
        presets = []
        if presets_file.exists():
            try:
                with open(presets_file, "r") as f:
                    presets = json.load(f)
            except Exception as e:
                print("Error loading presets, starting new.")
        presets.append(preset)
        try:
            with open(presets_file, "w") as f:
                json.dump(presets, f, indent=4)
            self.update_preset_list()
            messagebox.showinfo("Preset Saved", f"Preset '{preset_name}' saved successfully.")
        except Exception as e:
            print(f"Error saving preset: {e}")
    
    def load_preset(self, event=None):
        """Load the selected preset."""
        presets_file = self.data_dir / "presets.json"
        if presets_file.exists():
            try:
                with open(presets_file, "r") as f:
                    presets = json.load(f)
                selected = self.preset_var.get()
                for preset in presets:
                    if preset["name"] == selected:
                        self.clock_in_time.set(preset.get("clock_in_time", "09:00"))
                        self.clock_out_time.set(preset.get("clock_out_time", "17:00"))
                        messagebox.showinfo("Preset Loaded", f"Preset '{selected}' loaded.")
                        break
            except Exception as e:
                print("Error loading preset:", e)
    
    def update_preset_list(self):
        """Update the presets dropdown list."""
        presets_file = self.data_dir / "presets.json"
        presets_list = []
        if presets_file.exists():
            try:
                with open(presets_file, "r") as f:
                    presets = json.load(f)
                presets_list = [preset["name"] for preset in presets]
            except Exception as e:
                print("Error updating preset list:", e)
        self.preset_dropdown['values'] = presets_list
    
    def start_animations(self):
        """Start dinosaur and countdown animations."""
        self.animate_dinosaur()
        #self.animate_countdown()
    
    def animate_dinosaur(self):
        """Animate the dinosaur by updating its position."""
        self.dino_position += self.dino_direction
        if self.dino_position > 20 or self.dino_position < 0:
            self.dino_direction *= -1
        self.draw_dinosaur()
        self.root.after(100, self.animate_dinosaur)
    
    def animate_countdown(self):
        """Animate the countdown timer."""
        # For demonstration, count down from 1 hour (3600 seconds) repeatedly
        total_seconds = 3600 - (int(time.time()) % 3600)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        countdown_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.countdown_canvas.itemconfig(self.countdown_text, text=countdown_str)
        progress = (3600 - total_seconds) / 3600 * 380
        self.countdown_canvas.coords(self.progress_bar, 10, 10, 10 + progress, 30)
        self.root.after(1000, self.animate_countdown)
    
    def update_time_remaining(self):
        """Update the display for the next reminder."""
        self.next_event_label.config(text="Next reminder in 1 hour")
        self.root.after(60000, self.update_time_remaining)  # update every minute
    
    def update_time_display(self):
        """Update the current time display."""
        now = datetime.datetime.now()
        if self.time_format.get() == '12-hour':
            current_time = now.strftime("%I:%M:%S %p")
        else:
            current_time = now.strftime("%H:%M:%S")
        self.time_display.config(text=current_time)
        self.root.after(1000, self.update_time_display)
    
    def start_reminders(self):
        """Start the reminder loop in a separate thread."""
        if self.reminder_thread is None or not self.reminder_thread.is_alive():
            self.reminder_thread = threading.Thread(target=self.reminder_loop, daemon=True)
            self.reminder_thread.start()
    
    def reminder_loop(self):
        """A simple loop to check the time and send notifications."""
        while self.is_running:
            now = datetime.datetime.now().strftime("%H:%M")
            if now == self.clock_in_time.get():
                show_notification("Clock In Reminder", "It's time to clock in!", root=self.root, icon_path=self.icon_path)
                self.reminder_count += 1
                self.update_counter()
                time.sleep(60)  # Avoid multiple notifications
            elif now == self.clock_out_time.get():
                show_notification("Clock Out Reminder", "It's time to clock out!", root=self.root, icon_path=self.icon_path)
                self.reminder_count += 1
                self.update_counter()
                time.sleep(60)
            time.sleep(10)
    
    def update_counter(self):
        """Update the animated counter display."""
        self.counter_canvas.itemconfig(self.count_display, text=str(self.reminder_count))
    
    def toggle_reminders(self):
        """Toggle the reminder system on or off."""
        self.is_running = not self.is_running
        if self.is_running:
            self.start_button.config(text="Stop Reminders")
            self.status_label.config(text="Reminders are active")
            self.start_reminders()
        else:
            self.start_button.config(text="Start Reminders")
            self.status_label.config(text="Reminders stopped")
    
    def on_close(self):
        """Handle application close: save data and exit."""
        self.save_data()
        self.root.destroy()
    
    def update_time_format(self, event=None):
        """Update UI based on selected time format."""
        if self.time_format.get() == '12-hour':
            if not self.clock_in_ampm.winfo_ismapped():
                self.clock_in_ampm.pack(side=tk.LEFT, padx=5)
            if not self.clock_out_ampm.winfo_ismapped():
                self.clock_out_ampm.pack(side=tk.LEFT, padx=5)
            self.format_hint.config(text="Format: HH:MM (12-hour)")
        else:
            if self.clock_in_ampm.winfo_ismapped():
                self.clock_in_ampm.pack_forget()
            if self.clock_out_ampm.winfo_ismapped():
                self.clock_out_ampm.pack_forget()
            self.format_hint.config(text="Format: HH:MM (24-hour)")
    
    def on_button_hover(self, event, button):
        """Change button color on hover."""
        button.config(bg=self.colors["highlight"])
    
    def on_button_leave(self, event, button):
        """Reset button color when not hovered."""
        button.config(bg=self.colors["primary"])
    
    def test_notification(self):
        """Test the notification system."""
        show_notification("Test Notification", "This is a test notification.", root=self.root, icon_path=self.icon_path)
    
        # Add these new methods inside your ClockReminderApp class

    def get_next_event(self):
        """Determine the next event (Clock In or Clock Out) and return its type and datetime."""
        now = datetime.datetime.now()
        today = now.date()
        try:
            if self.time_format.get() == '12-hour':
                clock_in_dt = datetime.datetime.combine(
                    today, 
                    datetime.datetime.strptime(self.clock_in_time.get() + " " + self.clock_in_ampm.get(), "%I:%M %p").time()
                )
                clock_out_dt = datetime.datetime.combine(
                    today, 
                    datetime.datetime.strptime(self.clock_out_time.get() + " " + self.clock_out_ampm.get(), "%I:%M %p").time()
                )
            else:
                clock_in_dt = datetime.datetime.combine(
                    today, 
                    datetime.datetime.strptime(self.clock_in_time.get(), "%H:%M").time()
                )
                clock_out_dt = datetime.datetime.combine(
                    today, 
                    datetime.datetime.strptime(self.clock_out_time.get(), "%H:%M").time()
                )
        except Exception as e:
            print("Error parsing time:", e)
            return None, None

        if now < clock_in_dt:
            return "Clock In", clock_in_dt
        elif now < clock_out_dt:
            return "Clock Out", clock_out_dt
        else:
            # After clock out, next event is tomorrow's Clock In.
            tomorrow = today + datetime.timedelta(days=1)
            if self.time_format.get() == '12-hour':
                next_clock_in = datetime.datetime.combine(
                    tomorrow, 
                    datetime.datetime.strptime(self.clock_in_time.get() + " " + self.clock_in_ampm.get(), "%I:%M %p").time()
                )
            else:
                next_clock_in = datetime.datetime.combine(
                    tomorrow, 
                    datetime.datetime.strptime(self.clock_in_time.get(), "%H:%M").time()
                )
            return "Clock In", next_clock_in

    def get_previous_event(self):
        """Determine the previous event (used for progress bar calculation)."""
        now = datetime.datetime.now()
        today = now.date()
        try:
            if self.time_format.get() == '12-hour':
                clock_in_dt = datetime.datetime.combine(
                    today, 
                    datetime.datetime.strptime(self.clock_in_time.get() + " " + self.clock_in_ampm.get(), "%I:%M %p").time()
                )
                clock_out_dt = datetime.datetime.combine(
                    today, 
                    datetime.datetime.strptime(self.clock_out_time.get() + " " + self.clock_out_ampm.get(), "%I:%M %p").time()
                )
            else:
                clock_in_dt = datetime.datetime.combine(
                    today, 
                    datetime.datetime.strptime(self.clock_in_time.get(), "%H:%M").time()
                )
                clock_out_dt = datetime.datetime.combine(
                    today, 
                    datetime.datetime.strptime(self.clock_out_time.get(), "%H:%M").time()
                )
        except Exception as e:
            print("Error parsing time:", e)
            return None, None

        if now < clock_in_dt:
            # Previous event is yesterday's Clock Out.
            yesterday = today - datetime.timedelta(days=1)
            if self.time_format.get() == '12-hour':
                prev_event = datetime.datetime.combine(
                    yesterday, 
                    datetime.datetime.strptime(self.clock_out_time.get() + " " + self.clock_out_ampm.get(), "%I:%M %p").time()
                )
            else:
                prev_event = datetime.datetime.combine(
                    yesterday, 
                    datetime.datetime.strptime(self.clock_out_time.get(), "%H:%M").time()
                )
            return "Clock Out", prev_event
        elif now < clock_out_dt:
            return "Clock In", clock_in_dt
        else:
            return "Clock Out", clock_out_dt

    def update_time_remaining(self):
        """Update the countdown timer and progress bar until the next event."""
        event_type, event_time = self.get_next_event()
        if event_time is None:
            self.next_event_label.config(text="Invalid time format")
            self.root.after(1000, self.update_time_remaining)
            return

        now = datetime.datetime.now()
        remaining = event_time - now
        total_seconds = int(remaining.total_seconds())
        if total_seconds < 0:
            total_seconds = 0
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        countdown_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.next_event_label.config(text=f"Next {event_type} in {countdown_str}")

        # Update progress bar based on the interval from the previous event.
        prev_event_type, prev_event_time = self.get_previous_event()
        if prev_event_time is not None:
            total_interval = (event_time - prev_event_time).total_seconds()
            elapsed = (now - prev_event_time).total_seconds()
            progress = (elapsed / total_interval) * 380  # 380 is the total width for the progress bar.
            if progress > 380:
                progress = 380
            self.countdown_canvas.coords(self.progress_bar, 10, 10, 10 + progress, 30)

        self.root.after(1000, self.update_time_remaining)

    
    def create_scrollable_area(self):
        """Create a scrollable area for the main content."""
        # Create a canvas that fills the window
        self.scroll_canvas = tk.Canvas(self.root, bg=self.colors["background"])
        self.scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create a vertical scrollbar linked to the canvas
        v_scrollbar = tk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.scroll_canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scroll_canvas.configure(yscrollcommand=v_scrollbar.set)
        
        # Create a frame inside the canvas to hold your widgets
        self.main_frame = tk.Frame(self.scroll_canvas, bg=self.colors["background"])
        self.scroll_canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        
        # Update the scroll region whenever the size of main_frame changes
        self.main_frame.bind("<Configure>", lambda e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all")))
        
        # Bind mouse wheel events to the canvas (works on Windows)
        self.scroll_canvas.bind_all("<MouseWheel>", self._on_mousewheel)



# ========================================================================================
# MAIN EXECUTION
# ========================================================================================
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main window while checking dependencies
    check_dependencies()
    root.deiconify()  # Show the main window
    app = ClockReminderApp(root)
    root.mainloop()
