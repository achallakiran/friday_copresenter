import sys
import json
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

class PresentationTimer(QWidget):
    def __init__(self):
        super().__init__()
        self.load_settings()
        
        # 1. Window Setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(self.settings.get("opacity", 0.8))

        # 2. Logic Setup
        self.time_left = self.settings.get("total_minutes", 1) * 60
        self.old_pos = None

        # 3. UI Layout
        self.layout = QVBoxLayout()
        self.label = QLabel("00:00")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-family: 'Helvetica Neue', sans-serif;
                font-size: {self.settings.get('font_size', 90)}px;
                font-weight: bold;
                background-color: rgba(0, 0, 0, 100);
                border-radius: 15px;
                padding: 10px;
            }}
        """)
        
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        # 4. Timer Loop
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)
        self.update_display()

    def load_settings(self):
        try:
            with open("timer_config.json", "r") as f:
                self.settings = json.load(f)
        except Exception:
            self.settings = {"total_minutes": 1, "warning_minutes": 0.5, "font_size": 90, "opacity": 0.8}

    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
        
        # --- FIX: Force Timer to stay on top of Subtitles ---
        self.raise_()
        
        self.update_display()
        self.check_warnings()

    def update_display(self):
        minutes, seconds = divmod(self.time_left, 60)
        self.label.setText(f"{minutes:02}:{seconds:02}")

    def check_warnings(self):
        warning_limit = self.settings.get("warning_minutes", 0.5) * 60
        if self.time_left <= warning_limit and self.time_left > 0:
            self.label.setStyleSheet(self.label.styleSheet().replace("color: white;", "color: #FFD700;"))
        elif self.time_left == 0:
            self.label.setText("WRAP UP!")
            self.label.setStyleSheet(self.label.styleSheet().replace("color: #FFD700;", "color: #FF4500;"))

    # --- Mouse Events ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseDoubleClickEvent(self, event):
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    timer = PresentationTimer()
    timer.show()
    sys.exit(app.exec())
