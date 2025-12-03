import random
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QColor, QPainter, QBrush

class VoiceWorker(QThread):
    text_received = pyqtSignal(str)
    
    def __init__(self, speech_in):
        super().__init__()
        self.speech_in = speech_in
        self.running = True

    def run(self):
        print("VoiceWorker: Thread started.")
        while self.running:
            # print("VoiceWorker: Calling listen()...") # Reduce spam
            text = self.speech_in.listen()
            if text:
                self.text_received.emit(text)

class CommandProcessor(QThread):
    response_received = pyqtSignal(object)
    
    def __init__(self, router, text):
        super().__init__()
        self.router = router
        self.text = text
        
    def run(self):
        print(f"Processor: Routing '{self.text}'...")
        response = self.router.route(self.text)
        self.response_received.emit(response)

class PulsingIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 50)
        self.color = QColor(100, 100, 100) # Default Gray
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(100)
        self.pulse_size = 20
        self.growing = True

    def set_color(self, color):
        self.color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.NoPen)
        
        # Pulse animation logic
        if self.growing:
            self.pulse_size += 1
            if self.pulse_size >= 40:
                self.growing = False
        else:
            self.pulse_size -= 1
            if self.pulse_size <= 20:
                self.growing = True
                
        center = self.rect().center()
        painter.drawEllipse(center, self.pulse_size // 2, self.pulse_size // 2)

class JarvisGUI(QMainWindow):
    # States
    STATE_SLEEPING = "sleeping"
    STATE_LISTENING = "listening"
    STATE_PROCESSING = "processing"
    STATE_SPEAKING = "speaking"

    def __init__(self, router, speech_in, speech_out):
        print("GUI: Initializing...")
        super().__init__()
        self.router = router
        self.speech_in = speech_in
        self.speech_out = speech_out
        self.current_state = self.STATE_LISTENING # Default state
        
        self.setWindowTitle("Jarvis AI")
        self.setGeometry(100, 100, 400, 600)
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Indicator
        self.indicator = PulsingIndicator()
        layout.addWidget(self.indicator, alignment=Qt.AlignCenter)
        
        # Chat History
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)
        
        # Input Field
        self.input_field = QLineEdit()
        self.input_field.returnPressed.connect(self.process_text_input)
        layout.addWidget(self.input_field)
        
        # Listen Button (Hidden mostly now, but kept for manual control)
        self.listen_button = QPushButton("Stop Listening")
        self.listen_button.clicked.connect(self.toggle_listening)
        layout.addWidget(self.listen_button)
        
        # Voice Worker
        self.worker = VoiceWorker(self.speech_in)
        self.worker.text_received.connect(self.process_voice_input)
        self.is_listening = True # Start listening by default
        self.worker.start()
        
        print("GUI: Initialization complete.")
        
        # Auto-start greet
        self.set_state(self.STATE_SPEAKING)
        self.speech_out.speak("Jarvis is online. I am listening.")
        self.set_state(self.STATE_LISTENING)

    def set_state(self, state):
        self.current_state = state
        if state == self.STATE_SLEEPING:
            self.indicator.set_color(QColor(100, 100, 100)) # Gray
            self.listen_button.setText("Wake Up")
        elif state == self.STATE_LISTENING:
            self.indicator.set_color(QColor(0, 255, 0)) # Green
            self.listen_button.setText("Stop Listening")
        elif state == self.STATE_PROCESSING:
            self.indicator.set_color(QColor(0, 0, 255)) # Blue
        elif state == self.STATE_SPEAKING:
            self.indicator.set_color(QColor(255, 165, 0)) # Orange

    def append_message(self, sender, message):
        self.chat_history.append(f"<b>{sender}:</b> {message}")

    def process_text_input(self):
        text = self.input_field.text()
        if not text:
            return
        self.input_field.clear()
        self.append_message("You", text)
        self.start_processing(text)

    def process_voice_input(self, text):
        text_lower = text.lower()
        
        # Interrupt Logic: If user speaks while bot is speaking
        if self.current_state == self.STATE_SPEAKING:
            if "stop" in text_lower:
                self.speech_out.stop()
                self.set_state(self.STATE_LISTENING)
                self.append_message("System", "Speech interrupted.")
                return

        # Wake Word Logic
        if self.current_state == self.STATE_SLEEPING:
            if "hey jarvis" in text_lower or "wake up" in text_lower:
                self.wake_up()
            return

        # Sleep Command
        if "stop listening" in text_lower or "go to sleep" in text_lower:
            self.go_to_sleep()
            return

        self.append_message("You (Voice)", text)
        self.start_processing(text)

    def wake_up(self):
        greetings = [
            "I'm back online, sir.",
            "Systems operational. Ready for command.",
            "At your service.",
            "Hello again! What's the plan?"
        ]
        greeting = random.choice(greetings)
        self.set_state(self.STATE_SPEAKING)
        self.speech_out.speak(greeting)
        self.set_state(self.STATE_LISTENING)

    def go_to_sleep(self):
        self.set_state(self.STATE_SPEAKING)
        self.speech_out.speak("Going to sleep mode. Say 'Hey Jarvis' to wake me.")
        self.set_state(self.STATE_SLEEPING)

    def start_processing(self, text):
        self.set_state(self.STATE_PROCESSING)
        self.append_message("System", "Thinking...")
        self.processor = CommandProcessor(self.router, text)
        self.processor.response_received.connect(self.handle_response)
        self.processor.start()

    def handle_response(self, response):
        reply = response.get('reply', "I executed the action.")
        self.append_message("Jarvis", reply)
        
        self.set_state(self.STATE_SPEAKING)
        self.speech_out.speak(reply)
        
        # Return to listening state after speaking (unless manually stopped)
        if self.current_state != self.STATE_SLEEPING:
            self.set_state(self.STATE_LISTENING)

    def toggle_listening(self):
        if self.current_state == self.STATE_SLEEPING:
            self.wake_up()
        else:
            self.go_to_sleep()
