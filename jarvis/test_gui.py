from PyQt5.QtWidgets import QApplication, QLabel
import sys

app = QApplication(sys.argv)
label = QLabel("Hello World")
label.show()
print("GUI Started")
sys.exit(app.exec_())
