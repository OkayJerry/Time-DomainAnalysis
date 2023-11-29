from PyQt6.QtWidgets import QGroupBox, QPushButton, QSpinBox, QHBoxLayout
from PyQt6.QtCore import QTimer, Qt

# Global constants for the clock widget
GROUPBOX_TEXT = "Clock"
TOGGLE_BUTTON_SIZE = (25, 25)  # (width, height)
START_TEXT = "▶"
STOP_TEXT = "■"
SPINBOX_SUFFIX = " Hz"
SPINBOX_MIN = 1
SPINBOX_ALIGNMENT = Qt.AlignmentFlag.AlignCenter


class Clock(QGroupBox):
    """
    Custom clock widget with a frequency-adjustable timer.

    Attributes:
        timer (QTimer): Timer for controlling clock updates.
        hz_spinbox (QSpinBox): Spinbox for adjusting the clock frequency.
        toggle_button (QPushButton): Button for starting/stopping the clock.

    Methods:
        __init__: Initializes the Clock widget with layout and components.
        toggle: Toggles the state of the clock (start/stop).
        reset: Resets the clock frequency to the default value and stops the timer.
    """
    def __init__(self):
        """
        Initializes a new Clock instance.
        """
        super().__init__(GROUPBOX_TEXT)
        
        # Timer for clock updates
        self.timer = QTimer()
        
        # Spinbox for adjusting clock frequency
        self.hz_spinbox = QSpinBox()
        self.hz_spinbox.valueChanged.connect(lambda hz: self.timer.setInterval(int(1000 / hz)))
        self.hz_spinbox.setSuffix(SPINBOX_SUFFIX)
        self.hz_spinbox.setMinimum(SPINBOX_MIN)
        self.hz_spinbox.setAlignment(SPINBOX_ALIGNMENT)
        
        # Button for starting/stopping the clock
        self.toggle_button = QPushButton()
        self.toggle_button.setText(START_TEXT)
        self.toggle_button.setFixedSize(TOGGLE_BUTTON_SIZE[0], TOGGLE_BUTTON_SIZE[1])
        self.toggle_button.pressed.connect(self.hz_spinbox.clearFocus)
        self.toggle_button.pressed.connect(self.toggle)
        
        # Set up the layout
        layout = QHBoxLayout()
        layout.addWidget(self.hz_spinbox)
        layout.addWidget(self.toggle_button)
        self.setLayout(layout)
                
    def toggle(self):
        """
        Toggles the state of the clock (start/stop).
        """
        if self.timer.isActive():
            self.toggle_button.setText(START_TEXT)
            self.timer.stop()
        else:
            self.toggle_button.setText(STOP_TEXT)
            self.timer.start()
            
    def reset(self):
        """
        Resets the clock frequency to the default value and stops the timer.
        """
        self.hz_spinbox.setValue(1)
        if self.timer.isActive():
            self.toggle()