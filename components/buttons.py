from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import pyqtSignal

class TogglePlayButton(QPushButton):
    toggled = pyqtSignal(bool)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.is_playing: bool = False
        
        self.setText("▶")
        self.setFixedSize(25, 25)
        
        self.clicked.connect(self.toggle)
        
    def toggle(self) -> None:
        self.setText("▶" if self.is_playing else "⏹")
        self.is_playing = not self.is_playing
        self.toggled.emit(self.is_playing)
        