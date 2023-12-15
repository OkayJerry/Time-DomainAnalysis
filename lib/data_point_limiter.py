from PyQt6.QtWidgets import QGroupBox, QSlider, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt

LABEL_TEXT = "Number of Data Points: "
MINIMUM = 3
MAXIMUM = 1000

class DataPointLimiter(QGroupBox):
    """
    Custom QGroupBox to limit the number of data points.

    Attributes:
        slider (QSlider): Slider to set the number of data points.
    
    Signals:
        valueChanged(int): Signal emitted when the slider value changes.

    Methods:
        _onValueChanged: Slot to handle the valueChanged signal and update the group box title.
        getValue: Get the current value of the slider.
    """
    def __init__(self):
        """
        Initializes a new DataPointLimiter instance.
        """
        
        super().__init__()

        # Set the initial title of the group box
        self.setTitle(LABEL_TEXT + "All")
        
        # Create a horizontal slider to control the number of data points
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(MINIMUM)
        self.slider.setMaximum(MAXIMUM)
        self.slider.setValue(self.slider.maximum())
        
        # Connect the valueChanged signal of the slider to the _onValueChanged slot
        self.slider.valueChanged.connect(self._onValueChanged)
        
        # Create a horizontal layout and add the slider to it
        layout = QHBoxLayout()
        layout.addWidget(self.slider)
        self.setLayout(layout)
                
    def _onValueChanged(self, value: int):
        """
        Slot to handle the valueChanged signal of the slider.
        
        If the slider value is equal to its maximum, set the group box title to "All".
        Otherwise, set the group box title to "Number of Data Points: {value}".

        Parameters:
            value (int): The new value of the slider.
        """
        if value == self.slider.maximum():
            self.setTitle(LABEL_TEXT + "All")
        else:
            self.setTitle(LABEL_TEXT + str(value))

    def getValue(self) -> int:
        """
        Get the current value of the slider.

        Returns:
            int: The current value of the slider. If the value is equal to the maximum, return 0.
        """
        value = self.slider.value()
        return value if value != self.slider.maximum() else 0
