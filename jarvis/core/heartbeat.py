import threading
import time
import psutil
import datetime
from actions import vision_actions

class Heartbeat:
    def __init__(self, audio_engine):
        self.audio_engine = audio_engine
        self.running = False
        self.thread = None
        
        # Thresholds
        self.CPU_THRESHOLD = 85.0
        self.RAM_THRESHOLD = 90.0
        
        # Throttling proactive speech (cooldowns)
        self.last_posture_alert = 0
        self.POSTURE_COOLDOWN = 300 # 5 minutes
        
        self.last_system_alert = 0
        self.SYSTEM_COOLDOWN = 600 # 10 minutes
        
        self.last_volume_set = 0
        self.last_volume_time = 0

        print("Heartbeat: Monitoring system initialized.")

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print("Heartbeat: Thread started.")

    def stop(self):
        self.running = False

    def _monitor_loop(self):
        while self.running:
            # 1. Check Vision Context (Gestures and Posture)
            vision_context = vision_actions.get_vision_context()
            
            # Gesture handling
            if "giving a thumbs up" in vision_context.lower():
                now = time.time()
                # Cooldown for acknowledgment
                if now - self.last_system_alert > 10: 
                    self.audio_engine.tts.start_tts_stream("Acknowledged, sir.")
                    self.last_system_alert = now

            if "STOP" in vision_context:
                print("Heartbeat: Stop gesture detected.")
                self.audio_engine.tts.stop_tts_stream()

            # Posture check
            if "user is slouching" in vision_context.lower():
                now = time.time()
                if now - self.last_posture_alert > self.POSTURE_COOLDOWN:
                    print("Heartbeat Trigger: Posture")
                    self.audio_engine.tts.start_tts_stream("Sir, if I may, your posture is a bit compromised. You might want to sit up straight.")
                    self.last_posture_alert = now

            # 2. Real-time Gesture Actions (Volume Control)
            gesture_res = vision_actions.get_latest_gesture()
            if gesture_res and gesture_res.get("success") and gesture_res.get("gesture") == "POINTING":
                y = gesture_res.get("details", {}).get("y", 0.5)
                # Map Y (0.0 top to 1.0 bottom) to Volume (100 to 0)
                target_vol = int((1.0 - y) * 100)
                target_vol = max(0, min(100, target_vol))
                
                # Update if change is significant (> 5%) and not too frequent
                if abs(target_vol - self.last_volume_set) > 5 and time.time() - self.last_volume_time > 0.5:
                    from actions import system_actions
                    system_actions.set_volume(target_vol)
                    self.last_volume_set = target_vol
                    self.last_volume_time = time.time()
                    print(f"Heartbeat: Gesture Volume adjusted to {target_vol}%")

            # 3. Check System Metrics (Every ~10s)
            cpu_usage = psutil.cpu_percent()
            ram_usage = psutil.virtual_memory().percent
            
            if cpu_usage > self.CPU_THRESHOLD or ram_usage > self.RAM_THRESHOLD:
                now = time.time()
                if now - self.last_system_alert > self.SYSTEM_COOLDOWN:
                    msg = "Sir, the system is under heavy load. "
                    if cpu_usage > self.CPU_THRESHOLD: msg += f"CPU usage is at {cpu_usage:.0f} percent. "
                    if ram_usage > self.RAM_THRESHOLD: msg += f"Internal memory is at {ram_usage:.0f} percent. "
                    msg += "I recommend closing some resource-intensive applications."
                    
                    print("Heartbeat Trigger: System Resource")
                    self.audio_engine.tts.start_tts_stream(msg)
                    self.last_system_alert = now

            # 3. Check Battery (if laptop)
            battery = psutil.sensors_battery()
            if battery and battery.percent < 15 and not battery.power_plugged:
                 now = time.time()
                 if now - self.last_system_alert > 1200: # 20 mins
                    print("Heartbeat Trigger: Battery")
                    self.audio_engine.tts.start_tts_stream(f"Apologies, Sir, but our power reserves are critical. Battery is at {battery.percent} percent.")
                    self.last_system_alert = now

            time.sleep(0.5) # Faster loop for gestures, but we'll throttle heavy checks

def start_heartbeat(audio_engine):
    hb = Heartbeat(audio_engine)
    hb.start()
    return hb
