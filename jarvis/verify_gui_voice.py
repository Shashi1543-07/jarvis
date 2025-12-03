import sys
import pyttsx3
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel

print("Initializing pyttsx3...")
engine = pyttsx3.init()
print("pyttsx3 initialized.")

print("Initializing QApplication...")
app = QApplication(sys.argv)
print("QApplication initialized.")

class TestWindow(QMainWindow):
    def __init__(self):
        print("Window __init__ start")
        super().__init__()
        print("Window super().__init__ done")
        self.setWindowTitle("Test")
        self.setGeometry(100, 100, 200, 200)
        label = QLabel("Hello", self)
        label.move(50, 50)
        print("Window initialized")

print("Creating Window...")
window = TestWindow()
window.show()

print("Speaking...")
engine.say("Hello world")
engine.runAndWait()
print("Spoken.")

print("Starting Exec...")
sys.exit(app.exec_())
