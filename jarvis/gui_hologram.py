import sys
import os
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt, pyqtSlot, QMetaObject, Q_ARG
from PyQt5.QtGui import QFont

class JarvisGUI(QMainWindow):
    def __init__(self, engine=None):
        super().__init__()
        self.engine = engine
        
        # Window setup
        self.setWindowTitle("Jarvis AI - Holographic Interface")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: black;")
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 1. Hologram Area (WebEngine)
        self.web_view = QWebEngineView()
        # Ensure path is absolute
        html_path = os.path.abspath("jarvis/web/face_image.html")
        self.web_view.setUrl(QUrl.fromLocalFile(html_path))
        self.web_view.setStyleSheet("background: transparent;")
        layout.addWidget(self.web_view, stretch=8)
        
        # 2. Status Bar
        self.status_label = QLabel("SYSTEM STATE: INITIALIZING")
        self.status_label.setStyleSheet("color: cyan; font-family: Consolas; font-size: 14px; border: 1px solid cyan; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # 3. Chat Area
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("background-color: #111; color: cyan; font-family: Consolas; border: 1px solid cyan;")
        layout.addWidget(self.chat_area, stretch=2)
        
        # 4. Input Area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type command or use voice...")
        self.input_field.setStyleSheet("background-color: #222; color: cyan; font-family: Consolas; padding: 5px; border: 1px solid cyan;")
        self.input_field.returnPressed.connect(self.handle_text_input)
        input_layout.addWidget(self.input_field)
        
        self.listen_button = QPushButton("Stop Listening")
        self.listen_button.setStyleSheet("background-color: cyan; color: black; font-family: Consolas; font-weight: bold; padding: 5px;")
        self.listen_button.clicked.connect(self.toggle_listening)
        input_layout.addWidget(self.listen_button)
        
        layout.addLayout(input_layout)
        
        # Subscribe to Engine State
        if self.engine:
            self.engine.state_machine.on_state_change = self.update_state_from_engine
            self.engine.on_text_update = self.update_text_from_engine
            
        self.current_state = "IDLE"
        self.page_loaded = False
        self.web_view.loadFinished.connect(self.on_load_finished)
        # self.update_state("IDLE") # Don't update until loaded

    def on_load_finished(self):
        print("GUI: Page loaded.")
        self.page_loaded = True
        self.update_state(self.current_state)

    def update_state_from_engine(self, state):
        # Thread-safe update
        QMetaObject.invokeMethod(self, "_thread_safe_set_state", Qt.QueuedConnection, Q_ARG(str, state))

    @pyqtSlot(str)
    def _thread_safe_set_state(self, state):
        self.update_state(state)
    
    def update_text_from_engine(self, speaker, text):
        """Called by AudioEngine when text is exchanged"""
        QMetaObject.invokeMethod(self, "_thread_safe_append_text", Qt.QueuedConnection, 
                                Q_ARG(str, speaker), Q_ARG(str, text))
    
    @pyqtSlot(str, str)
    def _thread_safe_append_text(self, speaker, text):
        if speaker == "user":
            self.chat_area.append(f"<span style='color: #00ff00;'>You:</span> {text}")
        else:
            self.chat_area.append(f"<span style='color: #00e5ff;'>Jarvis:</span> {text}")

    def update_state(self, state):
        self.current_state = state
        self.status_label.setText(f"SYSTEM STATE: {state}")
        
        if not self.page_loaded:
            return

        # Update Avatar via JS
        js_code = ""
        if state == "LISTENING":
            js_code = "setState('listening');"
            self.listen_button.setText("Stop Listening")
        elif state == "THINKING":
            js_code = "setState('thinking');"
        elif state == "SPEAKING":
            js_code = "setState('speaking');"
        elif state == "IDLE":
            js_code = "setState('idle');"
            self.listen_button.setText("Start Listening")
            
        if js_code:
            self.web_view.page().runJavaScript(js_code)

    def handle_text_input(self):
        text = self.input_field.text()
        if text:
            self.chat_area.append(f"You: {text}")
            self.input_field.clear()
            
            if self.engine:
                # Manually trigger thinking state
                self.engine.state_machine.set_state("THINKING")
                threading.Thread(target=self._process_text_input, args=(text,)).start()

    def _process_text_input(self, text):
        if self.engine:
            response = self.engine.router.route(text)
            reply = response.get("text")
            if reply:
                self.engine.state_machine.set_state("SPEAKING")
                self.engine.tts.start_tts_stream(reply)
            else:
                self.engine.state_machine.set_state("IDLE")

    def toggle_listening(self):
        if self.engine:
            if self.current_state == "LISTENING":
                self.engine.state_machine.set_state("IDLE")
            else:
                self.engine.state_machine.set_state("LISTENING")

    def closeEvent(self, event):
        """Cleanup when window is closed"""
        print("GUI: Closing...")
        if self.engine:
            # Safely disconnect callbacks
            self.engine.state_machine.on_state_change = None
            self.engine.on_text_update = None
        event.accept()
