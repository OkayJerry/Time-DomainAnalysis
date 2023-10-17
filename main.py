import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QVBoxLayout, QGroupBox, QSpinBox
from PyQt6.QtCore import Qt, QThread

from components.Canvas import DynamicCanvas
from components.PVEditor import PVEditor
from components.PVEditor import TogglePlayButton
from components.Clock import Clock
from components.Processor import PVProcessor
from components.MenuBar import MenuBar

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Time-Domain Analysis")
        
        self.initializeWidgets()
        self.connectWidgets()
        
        self.setMenuBar(MenuBar(self))
        
    def initializeWidgets(self):        
        # Time-Domain Group Box
        self.canvas = DynamicCanvas()
        
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        time_domain_groupbox = QGroupBox("Time-Domain Plot")
        time_domain_groupbox.setLayout(layout)
        
        # Control Group Box
        self.toggle_play_button = TogglePlayButton()
        self.hz_spinbox = QSpinBox()
        self.hz_spinbox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.hz_spinbox.setSuffix(" Hz")
        self.hz_spinbox.setMinimum(1)
        
        layout = QHBoxLayout()
        layout.addWidget(self.hz_spinbox)
        layout.addWidget(self.toggle_play_button)
        controls_groupbox = QGroupBox("Controls")
        controls_groupbox.setLayout(layout)
        
        # PV Group Box
        self.pv_editor = PVEditor()
        
        layout = QVBoxLayout()
        layout.addWidget(self.pv_editor)
        pv_groupbox = QGroupBox("PV Editor")
        pv_groupbox.setLayout(layout)
        
        # Left-Side Widget
        layout = QVBoxLayout()
        layout.addWidget(controls_groupbox)
        layout.addWidget(pv_groupbox)
        left_widget = QWidget()
        left_widget.setLayout(layout)
        left_widget.setFixedWidth(450)

        # Main Layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(left_widget)
        main_layout.addWidget(time_domain_groupbox)
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(main_layout)
        
        self.clock = Clock()
        self.processor = PVProcessor(self.pv_editor.table, self.clock, self.canvas)
                
    def connectWidgets(self):
        def togglePlay(play: bool):                   
            if play:
                self.clock.updateInterval(self.hz_spinbox.value())
                self.clock.start()
            else:
                self.clock.stop()
        
        def removeFlaggedItems():
            self.clock.stop()
            self.processor.wait()
            self.pv_editor.table.removeFlaggedItems()
            self.clock.start()
        
        self.toggle_play_button.toggled.connect(togglePlay)
        self.hz_spinbox.valueChanged.connect(self.clock.updateInterval)
        self.clock.timeout.connect(lambda: self.processor.start() if not self.processor.isRunning() else None)
        self.processor.plotRequest.connect(self.addOrUpdateCurve)
        self.processor.requestCurveRemoval.connect(self.removeCurve)
        self.processor.removeFlaggedItems.connect(removeFlaggedItems)
        
        
    def addOrUpdateCurve(self, label, x, y, pen, subplot_index):  # Canvas must be updated from the main thread
        if self.canvas.getCurve(label):
            self.canvas.updateCurve(label, x, y, pen, subplot_index)
        else:
            self.canvas.addCurve(label, x, y, pen, subplot_index)
  
    def removeCurve(self, label: str):  # Canvas must be updated from the main thread
        self.canvas.removeCurve(label)
        
    def terminateProcesses(self):
        self.clock.stop()
        self.processor.wait()
                
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
