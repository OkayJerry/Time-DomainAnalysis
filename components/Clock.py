from PyQt6.QtCore import QTimer

class Clock(QTimer):
    def __init__(self):
        super().__init__()
        
    def updateInterval(self, hz: float):
        interval = int(1000 / hz)
        self.setInterval(interval)