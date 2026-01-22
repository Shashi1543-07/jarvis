import sys
import os
import threading
import time
import psutil
import subprocess
import platform
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QUrl, Qt, pyqtSlot, QMetaObject, Q_ARG, QObject, pyqtSignal, QThread, pyqtProperty

# Bridge for communication between Python and JavaScript
class Bridge(QObject):
    # Signals that will be exposed to JavaScript
    # NOTE: Signal names must match exactly what JavaScript expects
    # Using object type for all parameters to ensure QWebChannel compatibility
    stateChanged = pyqtSignal(str)
    audioDataChanged = pyqtSignal(float)
    systemStatsChanged = pyqtSignal(str)  # Use JSON string for complex objects
    chatMessageReceived = pyqtSignal(str, str)
    intentDetectedSignal = pyqtSignal(str, float)
    latencyUpdated = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._current_state = 'IDLE'
        self._last_stats = {}
        self._last_audio = 0.0
        print("Bridge: Initialized with signals")

        # Ensure signals are properly connected for QWebChannel
        self.stateChanged.connect(self._on_state_changed)
        self.audioDataChanged.connect(self._on_audio_data_changed)
        self.systemStatsChanged.connect(self._on_system_stats_changed)
        self.chatMessageReceived.connect(self._on_chat_message_received)
        self.intentDetectedSignal.connect(self._on_intent_detected)
        self.latencyUpdated.connect(self._on_latency_updated)

    def _on_state_changed(self, state):
        print(f"_on_state_changed called with: {state}")

    def _on_audio_data_changed(self, level):
        print(f"_on_audio_data_changed called with: {level}")

    def _on_system_stats_changed(self, stats):
        print(f"_on_system_stats_changed called with: {stats}")

    def _on_chat_message_received(self, sender, message):
        print(f"_on_chat_message_received called with: {sender}, {message}")

    def _on_intent_detected(self, intent_name, confidence):
        print(f"_on_intent_detected called with: {intent_name}, {confidence}")

    def _on_latency_updated(self, latency_ms):
        print(f"_on_latency_updated called with: {latency_ms}")

    # Properties for QWebChannel access
    @pyqtProperty(str)
    def currentStats(self):
        import json
        return json.dumps(self._last_stats)

    @pyqtProperty(str)
    def currentState(self):
        return self._current_state

    @pyqtProperty(float)
    def currentAudioLevel(self):
        return self._last_audio

    @pyqtSlot(result=str)
    def testMethod(self):
        """Simple test method to verify bridge is accessible"""
        print("Bridge.testMethod() called from JavaScript")
        return "Bridge connection OK"

    @pyqtSlot(str, result=str)
    def processTextCommand(self, text):
        """Process text command from JavaScript"""
        print(f"Bridge: Received text command from JavaScript: {text}")
        # This would typically trigger some action in the engine
        # For now, just return a confirmation
        return f"Processed: {text}"

    @pyqtSlot(result=str)
    def getCurrentState(self):
        """Return current state and metrics as JSON string"""
        print("Bridge: getCurrentState called from JavaScript")
        import json
        return json.dumps({
            "state": getattr(self, '_current_state', 'IDLE'),
            "stats": getattr(self, '_last_stats', {}),
            "audioLevel": getattr(self, '_last_audio', 0.0)
        })
    
    @pyqtSlot(result=str)
    def getState(self):
        """Get current state"""
        return getattr(self, '_current_state', 'IDLE')
    
    @pyqtSlot(result=str)
    def getStats(self):
        """Get current system stats as JSON string"""
        import json
        return json.dumps(getattr(self, '_last_stats', {}))
    
    @pyqtSlot(result=float)
    def getAudioLevel(self):
        """Get current audio level"""
        return getattr(self, '_last_audio', 0.0)

    # Expose methods that JavaScript can call to emit signals
    @pyqtSlot(str)
    def setState(self, state):
        """Emit state change signal"""
        print(f"Bridge: Emitting stateChanged signal with value: {state}")
        self._current_state = state
        self.stateChanged.emit(state)

    @pyqtSlot(float)
    def setAudioData(self, level):
        """Emit audio data signal"""
        print(f"Bridge: Emitting audioDataChanged signal with value: {level}")
        self._last_audio = level
        self.audioDataChanged.emit(level)

    @pyqtSlot(dict)
    def setSystemStats(self, stats):
        """Emit system stats signal"""
        print(f"Bridge: Emitting systemStatsChanged signal as JSON")
        self._last_stats = stats
        import json
        self.systemStatsChanged.emit(json.dumps(stats))

    @pyqtSlot(str, str)
    def sendChatMessage(self, sender, message):
        """Emit chat message signal"""
        print(f"Bridge: Emitting chatMessageReceived signal with values: {sender}, {message}")
        self.chatMessageReceived.emit(sender, message)

    @pyqtSlot(str, float)
    def setIntent(self, intent_name, confidence):
        """Emit intent detected signal"""
        print(f"Bridge: Emitting intentDetectedSignal with values: {intent_name}, {confidence}")
        self.intentDetectedSignal.emit(intent_name, confidence)

    @pyqtSlot(int)
    def setLatency(self, latency_ms):
        """Emit latency update signal"""
        print(f"Bridge: Emitting latencyUpdated signal with value: {latency_ms}")
        self.latencyUpdated.emit(latency_ms)

class SystemMonitorThread(QThread):
    def __init__(self, bridge):
        super().__init__()
        self.bridge = bridge
        self.running = True

    def get_gpu_usage(self):
        """Get GPU usage if available"""
        try:
            # Try to get NVIDIA GPU info using nvidia-smi
            if platform.system() == "Windows":
                result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    gpu_info = result.stdout.strip().split(', ')
                    gpu_util = int(gpu_info[0])
                    return gpu_util
            elif platform.system() == "Linux":
                result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    gpu_info = result.stdout.strip().split(', ')
                    gpu_util = int(gpu_info[0])
                    return gpu_util
        except Exception:
            # Fallback for systems without NVIDIA GPUs or nvidia-smi
            pass

        # For other systems, return a simulated value or 0
        return 0

    def get_battery_status(self):
        """Get battery status if available"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                return battery.percent
            else:
                return 100  # Assume 100% if no battery (desktop)
        except Exception:
            return 100

    def get_temperature(self):
        """Get system temperature if available"""
        try:
            # Try to get temperature from sensors
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    # Get CPU temperature if available
                    for name, entries in temps.items():
                        if name.startswith(('coretemp', 'cpu_thermal', 'acpi')):
                            for entry in entries:
                                if 'Core' in entry.label or 'Tdie' in entry.label or entry.label == '':
                                    return round(entry.current)
                    # If no specific CPU temp found, return first available temp
                    for name, entries in temps.items():
                        for entry in entries:
                            return round(entry.current)
            return 40  # Default temperature if not available
        except Exception:
            return 40

    def get_internet_speed(self):
        """Get approximate internet speed"""
        try:
            # This is a simplified version - in a real implementation you'd want to run an actual speed test
            # For now, we'll return a simulated value based on network activity
            net_io = psutil.net_io_counters()
            # Calculate bytes sent/received per second over last interval
            # This is a very basic approximation
            return round(100.0, 1)  # Return a simulated value
        except Exception:
            return 0.0

    def run(self):
        while self.running:
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                gpu = self.get_gpu_usage()
                battery = self.get_battery_status()
                temperature = self.get_temperature()
                internet_speed = self.get_internet_speed()

                # Get core temperature if available
                core_temp = temperature + 5  # Approximate core temp as slightly higher than system temp

                # Simple online check
                net = "ONLINE" if psutil.net_if_stats() else "OFFLINE"

                stats = {
                    "cpu": cpu,
                    "ram": ram,
                    "gpu": gpu,
                    "network": net,
                    "internetSpeed": internet_speed,
                    "battery": battery,
                    "temperature": temperature,
                    "coreTemp": core_temp
                }
                # Call the method which will emit the signal
                self.bridge.setSystemStats(stats)
                print(f"DEBUG: Emitted system stats: CPU={stats['cpu']}%, RAM={stats['ram']}%")
                time.sleep(1) # Update every 1 second for smoother HUD
            except Exception as e:
                print(f"System Monitor Error: {e}")
                time.sleep(5)

class CustomWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        level_names = {
            QWebEnginePage.InfoMessageLevel: "INFO",
            QWebEnginePage.WarningMessageLevel: "WARNING",
            QWebEnginePage.ErrorMessageLevel: "ERROR"
        }
        level_str = level_names.get(level, "UNKNOWN")
        print(f"js: [{level_str}] {message} (line {line_number})")
        if level == QWebEnginePage.ErrorMessageLevel:
            import sys
            sys.stderr.write(f"JavaScript ERROR: {message}\n")

class JarvisGUI(QMainWindow):
    def __init__(self, engine=None):
        super().__init__()
        self.engine = engine

        # Window setup
        self.setWindowTitle("Jarvis AI - Iron Man Armor Suite")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: black;")

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. Hologram Area (WebEngine)
        self.web_view = QWebEngineView()
        
        # Use custom page for console logging
        self.custom_page = CustomWebEnginePage(self.web_view)
        self.web_view.setPage(self.custom_page)
        
        # Enable developer settings
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        
        # Point to the NEW HUD index.html with cache-busting
        
        # Point to the NEW HUD index.html with cache-busting
        html_path = os.path.abspath("ui/jarvis-hud/index.html")
        cache_bust = int(time.time() * 1000)
        url = QUrl.fromLocalFile(html_path)
        url.setQuery(f"v={cache_bust}")
        print(f"GUI: Loading HTML: {url.toString()}")
        self.web_view.setUrl(url)
        self.web_view.setStyleSheet("background: black;")

        # Custom Context Menu Policy to prevent right-click menu
        self.web_view.setContextMenuPolicy(Qt.NoContextMenu)

        layout.addWidget(self.web_view)

        # Setup WebChannel
        self.bridge = Bridge()
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        print("GUI: Bridge registered with QWebChannel")

        # Start System Monitor
        self.monitor_thread = SystemMonitorThread(self.bridge)
        self.monitor_thread.start()

        # Subscribe to Engine State
        if self.engine:
            # Register callbacks for all states or just use a generic transition logger
            for state in self.engine.state_machine._valid_transitions.keys():
                self.engine.state_machine.register_callback(state, self.handle_state_transition)
            self.engine.on_text_update = self.update_text_from_engine
            self.engine.on_audio_level = self.update_audio_level_from_engine
            self.engine.on_latency_update = self.update_latency_from_engine
            self.engine.on_intent_detected = self.update_intent_from_engine
            print("GUI: All AudioEngine callbacks registered successfully")

        self.current_state = "IDLE"
        self.page_loaded = False
        self.web_view.loadFinished.connect(self.on_load_finished)

    def on_load_finished(self, ok):
        if ok:
            print("GUI: Page loaded successfully (Neo-HUD).")
            # Inject a test script to verify JS execution
            self.web_view.page().runJavaScript("console.log('GUI DIAGNOSTIC: JavaScript is running!');")
        else:
            print("GUI: ERROR - Page failed to load!")
        self.page_loaded = ok
        if ok:
            self.update_state(self.current_state)

    def handle_state_transition(self, old_state, new_state):
        """Wrapper for state machine callback"""
        self.update_state_from_engine(new_state.value)

    def update_state_from_engine(self, state_value):
        # Thread-safe update
        QMetaObject.invokeMethod(self, "_thread_safe_set_state", Qt.QueuedConnection, Q_ARG(str, state_value))

    @pyqtSlot(str)
    def _thread_safe_set_state(self, state):
        self.update_state(state)

    def update_text_from_engine(self, speaker, text):
        """Called by AudioEngine when text is exchanged"""
        print(f"GUI: update_text_from_engine called - Speaker: {speaker}, Text: {text[:50]}...")
        try:
            self.bridge.sendChatMessage(speaker.upper(), text)
            print(f"GUI: Successfully emitted chatMessage signal for {speaker}")
        except Exception as e:
            print(f"GUI: ERROR emitting chatMessage: {e}")

    def update_audio_level_from_engine(self, level):
        """Called by AudioEngine with normalized RMS level"""
        try:
            self.bridge.setAudioData(level)
        except Exception as e:
            print(f"GUI: ERROR emitting setAudioData: {e}")

    def update_latency_from_engine(self, latency_ms):
        """Called by AudioEngine with response latency in milliseconds"""
        try:
            self.bridge.setLatency(latency_ms)
            print(f"GUI: Emitted latency update: {latency_ms}ms")
        except Exception as e:
            print(f"GUI: ERROR emitting latencyUpdate: {e}")

    def update_intent_from_engine(self, intent_name, confidence):
        """Called by AudioEngine/Router with detected intent"""
        try:
            self.bridge.setIntent(intent_name, confidence)
            print(f"GUI: Emitted intent: {intent_name} (confidence: {confidence:.2f})")
        except Exception as e:
            print(f"GUI: ERROR emitting intentDetected: {e}")

    def update_state(self, state):
        self.current_state = state

        if not self.page_loaded:
            print(f"GUI: State update deferred (page not loaded): {state}")
            return

        # Emit signal to JS via bridge
        print(f"GUI: Emitting state to JavaScript: {state}")
        try:
            self.bridge.setState(state.lower())
            print(f"GUI: Successfully emitted setState signal: {state}")
        except Exception as e:
            print(f"GUI: ERROR emitting setState: {e}")

    @pyqtSlot(str, dict, float)
    def updateJarvisState(self, state, metrics, audio):
        """Legacy method provided for compatibility if needed"""
        if state: self.update_state(state)
        if metrics: self.bridge.setSystemStats(metrics)
        if audio is not None: self.bridge.setAudioData(audio)

    def closeEvent(self, event):
        """Cleanup when window is closed"""
        print("GUI: Closing...")
        self.monitor_thread.running = False
        self.monitor_thread.wait()
        if self.engine:
            # Safely disconnect callbacks
            self.engine.state_machine.on_state_change = None
            self.engine.on_text_update = None
        event.accept()
