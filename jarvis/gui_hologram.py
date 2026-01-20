import sys
import os
import threading
import time
import psutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QUrl, Qt, pyqtSlot, QMetaObject, Q_ARG, QObject, pyqtSignal, QThread

# Bridge for communication between Python and JavaScript
class Bridge(QObject):
    setState = pyqtSignal(str)
    setAudioData = pyqtSignal(list)
    systemStats = pyqtSignal(dict) # Signal for CPU/RAM/Network
    chatMessage = pyqtSignal(str, str) # Signal for Chat (Speaker, Text)

    def __init__(self):
        super().__init__()

class SystemMonitorThread(QThread):
    def __init__(self, bridge):
        super().__init__()
        self.bridge = bridge
        self.running = True

    def run(self):
        while self.running:
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                # Simple online check
                net = "ONLINE" if psutil.net_if_stats() else "OFFLINE"
                
                stats = {
                    "cpu": cpu,
                    "ram": ram,
                    "network": net
                }
                self.bridge.systemStats.emit(stats)
                time.sleep(2) # Update every 2 seconds
            except Exception as e:
                print(f"System Monitor Error: {e}")
                time.sleep(5)

class JarvisGUI(QMainWindow):
    def __init__(self, engine=None):
        super().__init__()
        self.engine = engine
        
        # Window setup
        self.setWindowTitle("Jarvis AI - Stark Tech Interface")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: black;")
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Hologram Area (WebEngine)
        self.web_view = QWebEngineView()
        # Point to the NEW HUD index.html
        html_path = os.path.abspath("jarvis/web/index.html")
        self.web_view.setUrl(QUrl.fromLocalFile(html_path))
        self.web_view.setStyleSheet("background: black;")

        # Custom Context Menu Policy to prevent right-click menu
        self.web_view.setContextMenuPolicy(Qt.NoContextMenu)
        
        layout.addWidget(self.web_view)
        
        # Setup WebChannel
        self.bridge = Bridge()
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        
        # Start System Monitor
        self.monitor_thread = SystemMonitorThread(self.bridge)
        self.monitor_thread.start()
        
        # Subscribe to Engine State
        if self.engine:
            # Register callbacks for all states or just use a generic transition logger
            for state in self.engine.state_machine._valid_transitions.keys():
                self.engine.state_machine.register_callback(state, self.handle_state_transition)
            self.engine.on_text_update = self.update_text_from_engine
            
        self.current_state = "IDLE"
        self.page_loaded = False
        self.web_view.loadFinished.connect(self.on_load_finished)

    def on_load_finished(self):
        print("GUI: Page loaded.")
        self.page_loaded = True
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
        self.bridge.chatMessage.emit(speaker, text)
    
    def update_state(self, state):
        self.current_state = state
        
        if not self.page_loaded:
            return

        # Emit signal to JS via bridge
        self.bridge.setState.emit(state.lower())

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
