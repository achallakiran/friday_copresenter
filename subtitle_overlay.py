import tkinter as tk
import sys
import threading

class SubtitleOverlay:
    def __init__(self):
        self.root = tk.Tk()
        
        # Window Configuration
        self.root.title("Friday Subtitles")
        self.root.overrideredirect(True)  # Remove title bar/borders
        self.root.attributes('-topmost', True) # Always on top
        self.root.attributes('-alpha', 0.7) # Semi-transparent background
        
        # Geometry: Full width, bottom of screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        height = 100
        y_pos = screen_height - height - 50 # 50px padding from bottom
        self.root.geometry(f"{screen_width}x{height}+0+{y_pos}")
        self.root.configure(bg='black')

        # Label Configuration
        self.label = tk.Label(
            self.root, 
            text="Friday Listening...", 
            font=("Helvetica", 32, "bold"), 
            fg="white", 
            bg="black", 
            wraplength=screen_width-100
        )
        self.label.pack(expand=True, fill='both')

        # Timer to clear text
        self.clear_timer = None

        # Start input listener thread
        self.input_thread = threading.Thread(target=self.listen_stdin, daemon=True)
        self.input_thread.start()

        self.root.mainloop()

    def update_text(self, text):
        self.label.config(text=text)
        
        # --- FIX: Removed self.root.lift() ---
        # We rely on attributes('-topmost', True) set in __init__
        # This prevents the subtitle from fighting with the Timer overlay.

        # Reset clear timer
        if self.clear_timer:
            self.root.after_cancel(self.clear_timer)
        # Auto-clear text after 5 seconds
        self.clear_timer = self.root.after(5000, lambda: self.label.config(text=""))

    def listen_stdin(self):
        """Reads from standard input without blocking GUI"""
        for line in sys.stdin:
            text = line.strip()
            if text:
                # Schedule GUI update on main thread
                self.root.after(0, self.update_text, text)

if __name__ == "__main__":
    SubtitleOverlay()
