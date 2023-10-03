from PyQt6.QtWidgets import QDoubleSpinBox, QWidget, QRadioButton, QHBoxLayout
from PyQt6.QtCore import pyqtSignal, Qt

class OptionalDoubleSpinBox(QWidget):
    disableOtherRadioButtons = pyqtSignal()
    
    def __init__(self, initial_value: float, step: float = 0.25, comparator=lambda value: 0 <= value <= float("Inf")):
        super().__init__()
        
        if not comparator(initial_value):
            raise ValueError(f"Initial value must be within bounds.")
        
        self.prev_value = initial_value
        self.comparator = comparator
        
        self.ERROR = 1e-5
        
        self.radiobutton = QRadioButton()
        self.radiobutton.clicked.connect(lambda: self.disableOtherRadioButtons.emit())
        
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setValue(initial_value)
        self.spinbox.setSingleStep(step)
        self.spinbox.valueChanged.connect(self.onValueChanged)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.radiobutton)
        layout.addWidget(self.spinbox)
        self.setLayout(layout)
        
    
    def onValueChanged(self, value: float) -> None:
        self.spinbox.blockSignals(True)
        if not self.comparator(value - self.ERROR) or not self.comparator(value + self.ERROR):
            self.spinbox.setValue(self.prev_value)
        self.spinbox.blockSignals(False)
        
        self.prev_value = self.spinbox.value()
        
    def value(self):
        return self.spinbox.value() if self.radiobutton.isChecked() else None