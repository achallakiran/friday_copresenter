import json
import time
import subprocess
import threading
import sys
import os
import string
from speech_engine import SpeechListener
from datetime import datetime 
from llm_helper import get_llm

# --- AppleScript Helper ---
def run_applescript(script):
    args = ['osascript', '-e', script]
    try:
        result = subprocess.run(args, check=True, capture_output=True)
        return result
    except subprocess.CalledProcessError as e:
        return None

# --- PowerPoint Control Functions ---

def wait_for_slideshow_window(timeout=15):
    """Checks if the Slide Show window is active."""
    print("DEBUG: Waiting for slideshow window...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        script = '''
        tell application "Microsoft PowerPoint"
            if (count of slide show windows) > 0 then
                return "true"
            else
                return "false"
            end if
        end tell
        '''
        res = run_applescript(script)
        if res and "true" in res.stdout.decode().lower():
            time.sleep(1) 
            return True
        time.sleep(1)
    
    print("Error: Slide show window never appeared.")
    return False

def ppt_open(path):
    """Uses macOS native 'open' command."""
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        print(f"ERROR: File not found at {abs_path}")
        return

    print(f"DEBUG: Opening file via System Command: {abs_path}")
    subprocess.run(["open", abs_path])
    
    # --- TIMING FIX: Increased to 4s to ensure full load before focus ---
    time.sleep(4) 

def ppt_start_2():
    """Alternative start method."""
    run_applescript('tell application "Microsoft PowerPoint" to activate')
    
    script = '''
    tell application "Microsoft PowerPoint"
        activate
        if (count of presentations) > 0 then
            run slide show of active presentation
        end if
    end tell
    '''
    run_applescript(script)
    
    if wait_for_slideshow_window():
        print("Slideshow is active and ready.")
    else:
        print("Warning: Slideshow failed to start.")

def ppt_start():
    """
    Starts the slideshow by simulating the 'Command + Shift + Enter' shortcut.
    """
    print("DEBUG: Sending Slide Show shortcut...")
    
    # Activate PowerPoint first
    run_applescript('tell application "Microsoft PowerPoint" to activate')
    
    # --- TIMING FIX: Increased to 1.5s to allow focus switch ---
    time.sleep(1.5) 
    
    script = '''
    tell application "System Events"
        -- Command + Shift + Enter shortcut
        key code 36 using {command down, shift down}
    end tell
    '''
    run_applescript(script)
    
    # Verify the window exists before proceeding
    if wait_for_slideshow_window():
        print("Slideshow is active and ready.")
    else:
        print("Warning: Slideshow failed to start. Trying fallback...")
        run_applescript('tell application "Microsoft PowerPoint" to run slide show of active presentation')


def ppt_next():
    script = '''
    tell application "Microsoft PowerPoint"
        if (count of slide show windows) > 0 then
            go to next slide (slide show view of slide show window 1)
        end if
    end tell
    '''
    run_applescript(script)

def ppt_prev():
    script = '''
    tell application "Microsoft PowerPoint"
        if (count of slide show windows) > 0 then
            go to previous slide (slide show view of slide show window 1)
        end if
    end tell
    '''
    run_applescript(script)

def ppt_stop():
    script = '''
    tell application "Microsoft PowerPoint"
        if (count of slide show windows) > 0 then
            exit slide show (slide show view of slide show window 1)
        end if
    end tell
    '''
    run_applescript(script)

def ppt_goto(index):
    """
    Absolute Jump Fix: Maps numbers to Key Codes and ensures 
    sequential execution with proper delays.
    """
    key_codes = {
        '0': 29, '1': 18, '2': 19, '3': 20, '4': 21,
        '5': 23, '6': 22, '7': 26, '8': 28, '9': 25
    }
    
    str_index = str(index)
    key_commands = ""
    for digit in str_index:
        if digit in key_codes:
            key_commands += f"key code {key_codes[digit]}\n        delay 0.1\n        "

    # --- TIMING FIX: Delays increased to 1.0 and 0.8 ---
    script = f'''
    tell application "Microsoft PowerPoint" to activate
    delay 1.0 -- Wait for PPT to be the frontmost app
    
    tell application "System Events"
        {key_commands}
        
        delay 0.8 -- Wait for digits to register
        
        -- Press Enter (Key Code 36)
        key code 36
    end tell
    '''
    run_applescript(script)
    time.sleep(1)


# --- Main Presenter Logic ---

class FridayPresenter:
    def __init__(self):
        self.listener = SpeechListener()
        self.load_configs()
        self.llm = get_llm() #new method to load llm
        self.is_running = True
        self.auto_mode = False
        self.timer_process = None
        self.subtitle_process = None
 
        self.current_presentation_slides = [] 
        self.current_slide_ptr = 0 
        self.interrupt_event = threading.Event()

    def load_configs(self):
        try:
            with open("commands.json", "r") as f: self.commands = json.load(f)
            with open("slides_master.json", "r") as f: self.slides_master = json.load(f)
            with open("presentations.json", "r") as f: self.presentations = json.load(f)
            with open("tts_config.json", "r") as f: self.tts_config = json.load(f)
            print(f"Configs loaded. Voice: {self.tts_config.get('voice', 'Default')}")
        except FileNotFoundError as e:
            print(f"Error loading config: {e}")
            sys.exit(1)

    def speak_text(self, text):
        voice = self.tts_config.get("voice", "Zoe")
        rate = str(self.tts_config.get("rate", 180))
        proc = subprocess.Popen(["say", "-v", voice, "-r", rate, text])
        return proc

    def normalize_text(self, text):
        if not text: return ""
        text = text.translate(str.maketrans('', '', string.punctuation))
        return text.lower().strip()

    def start_timer_overlay(self):
        if self.timer_process is None or self.timer_process.poll() is not None:
            print("[*] Starting Timer Overlay...")
            self.timer_process = subprocess.Popen([sys.executable, "timer_overlay.py"])

    def stop_timer_overlay(self):
        if self.timer_process and self.timer_process.poll() is None:
            print("[*] Stopping Timer Overlay...")
            self.timer_process.terminate()
            self.timer_process = None

    # --- Subtitle Overlay Methods ---
    def start_subtitle_overlay(self):
        """Starts the subtitle overlay script and opens a pipe to it."""
        if self.subtitle_process is None or self.subtitle_process.poll() is not None:
            print("[*] Starting Subtitle Overlay...")
            
            # --- PATH FIX: Ensure we find the file relative to this script ---
            current_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(current_dir, "subtitle_overlay.py")
            
            if not os.path.exists(script_path):
                print(f"ERROR: Could not find subtitle_overlay.py at {script_path}")
                return

            self.subtitle_process = subprocess.Popen(
                [sys.executable, script_path],
                stdin=subprocess.PIPE,
                text=True, 
                bufsize=1   
            )

    def stop_subtitle_overlay(self):
        if self.subtitle_process and self.subtitle_process.poll() is None:
            print("[*] Stopping Subtitle Overlay...")
            self.subtitle_process.terminate()
            self.subtitle_process = None

    def update_subtitles(self, text):
        """Sends recognized text to the overlay process."""
        if self.subtitle_process and self.subtitle_process.poll() is None:
            try:
                self.subtitle_process.stdin.write(text + "\n")
                self.subtitle_process.stdin.flush()
            except BrokenPipeError:
                print("Subtitle process disconnected.")
                self.subtitle_process = None

    def match_command(self, text):
        clean_text = self.normalize_text(text)
        if not clean_text: return None
        for action, keywords in self.commands.items():
            for k in keywords:
                if k in clean_text:
                    return action
        return "unknown"

    def match_presentation_request(self, text):
        clean_text = self.normalize_text(text)
        triggers = ["start", "open", "launch"]
        if not any(t in clean_text for t in triggers):
            return None, None, None, None
        for name, data in self.presentations.items():
            if name in clean_text:
                return name, data.get("file"), data.get("sequence"), data.get("overview")
        return None, None, None, None

    def match_specific_slide(self, text):
        clean_text = self.normalize_text(text)
        text_words = set(clean_text.split())
        best_match = None
        max_matches = 0
        for slide_id, data in self.slides_master.items():
            keywords = set([k.lower() for k in data.get("keywords", [])])
            matches = len(text_words.intersection(keywords))
            if matches > 0 and matches > max_matches:
                max_matches = matches
                best_match = int(data['index'])
        return best_match

    def run_automation(self):
        print("--- Friday Automation Started (Say 'Interrupt' to stop) ---")
        while self.current_slide_ptr < len(self.current_presentation_slides):
            if self.interrupt_event.is_set(): break

            slide_idx = self.current_presentation_slides[self.current_slide_ptr]
            slide_data = self.slides_master.get(str(slide_idx))
            
            if not slide_data:
                print(f"Warning: No data for slide index {slide_idx}")
                self.current_slide_ptr += 1
                continue

            ppt_goto(slide_idx)
            
            print(f"Friday Speaking: {slide_data['spoken_text']}")
            speech_proc = self.speak_text(slide_data['spoken_text'])
            
            while speech_proc.poll() is None:
                if self.interrupt_event.is_set():
                    speech_proc.terminate() 
                    break
                time.sleep(0.1)

            if self.interrupt_event.is_set(): break

            wait_time = slide_data.get('duration', 2)
            for _ in range(wait_time):
                if self.interrupt_event.is_set(): break
                time.sleep(1)

            if self.interrupt_event.is_set(): break
            
            self.current_slide_ptr += 1
            if self.current_slide_ptr < len(self.current_presentation_slides):
                ppt_next()
            else:
                print("Presentation finished.")
                
        self.auto_mode = False
        self.interrupt_event.clear()
        print("--- Automation Ended ---")

    def take_photo(self):
        """Captures a photo using the connected camera."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"captures/townhall_{timestamp}.jpg"
        
        print(f"[*] Friday: Capturing photo to {filename}...")
        try:
            # -w 1.0 gives the camera 1 second to adjust focus/light
            subprocess.run(["imagesnap", "-w", "1.0", filename], check=True)
            self.speak_text("Photo captured.")
        except Exception as e:
            print(f"Error capturing photo: {e}")
            self.speak_text("I encountered an error while taking the photo.")


    def start(self):
        print("Friday Presenter Ready. Listening...")
        
        # Start subtitles immediately when Friday starts
        self.start_subtitle_overlay()

        while self.is_running:
            try:
                raw_text = self.listener.listen_once()
                if not raw_text: continue
                
                print(f"Debug Raw Text: {raw_text}") 
                
                # --- Update Subtitles with what was just heard ---
                self.update_subtitles(raw_text)

                action = self.match_command(raw_text)

                p_name, p_file, p_seq, p_overview = self.match_presentation_request(raw_text)

                # --- NEW TIMER COMMANDS ---
                if "start timer".strip(",") in raw_text.lower():
                    self.start_timer_overlay()
                    continue
                elif "stop timer".strip(",") in raw_text.lower():
                    self.stop_timer_overlay()
                    continue

                # --- NEW LLM COMMAND ---
                if "explain" in raw_text.lower():
                    # Extract the actual question part
                    # e.g. "Friday explain quantum physics" -> "quantum physics"
                    query = raw_text.lower().split("explain", 1)[1].strip()
                    
                    if query:
                        self.speak_text("Let me check that for you.")
                        response = self.llm.generate_response(query, p_overview)
                        print(f"Friday AI Answer: {response}")
                        
                        # Display on subtitle
                        self.update_subtitles(response) 
                        
                        # Speak result
                        speech_proc = self.speak_text(response)
                        
                        # Wait for speech to finish so we don't listen to ourselves
                        while speech_proc.poll() is None:
                            time.sleep(0.1)
                    continue

                if action == "take_photo":
                    self.take_photo()
                    continue
                
                if action == "interrupt":
                    print("!!! INTERRUPT RECEIVED !!!")
                    self.interrupt_event.set()
                    self.auto_mode = False
                    continue
                
                if self.auto_mode:
                    print(f"Ignored '{raw_text}' (Friday is active. Say 'Interrupt' to stop)")
                    continue

                #p_name, p_file, p_seq, p_overview = self.match_presentation_request(raw_text) # Changed position. moved up

                if p_name and p_file:
                    print(f"Opening presentation: {p_name}...")
                    self.current_presentation_slides = p_seq
                    self.current_slide_ptr = 0
                    ppt_open(p_file)     
                    ppt_start()          
                    ppt_goto(p_seq[0])   
                    continue

                if action == "next":
                    ppt_next()
                    if self.current_slide_ptr < len(self.current_presentation_slides) - 1:
                        self.current_slide_ptr += 1
                elif action == "previous":
                    ppt_prev()
                    if self.current_slide_ptr > 0:
                        self.current_slide_ptr -= 1
                elif action == "stop":
                    ppt_stop()
                elif action == "take_over":
                    if not self.current_presentation_slides:
                        print("Error: No active presentation sequence.")
                    else:
                        self.auto_mode = True
                        self.interrupt_event.clear()
                        t = threading.Thread(target=self.run_automation)
                        t.start()
                else:
                    target_slide = self.match_specific_slide(raw_text)
                    if target_slide:
                        print(f"Jumping to slide {target_slide}")
                        ppt_goto(target_slide)
                        if target_slide in self.current_presentation_slides:
                            self.current_slide_ptr = self.current_presentation_slides.index(target_slide)
                    elif action == "unknown":
                        print("Command not recognized.")

            except KeyboardInterrupt:
                self.is_running = False
                self.interrupt_event.set()
                self.stop_subtitle_overlay() # Cleanup subtitles
                print("\nGoodbye.")

if __name__ == "__main__":
    app = FridayPresenter()
    app.start()
