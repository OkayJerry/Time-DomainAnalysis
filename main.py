import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QVBoxLayout, QGroupBox, QSpinBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from components.DynamicCanvas import DynamicCanvas
from epics import PV
import time
import threading
from components.tools import ControlTree, PVEditor
from components.PVengine import PVEngine
from components.buttons import TogglePlayButton
import pandas as pd
from copy import deepcopy
from pyqtgraph import mkPen

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Time-Domain Analysis")
        
        self.initializeWidgets()
        self.connectWidgets()
        
        self.run_sim = False
        self.rolling_enabled = False
        self.ewm_enabled = False
        
        self._times = []
        
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
        
        self.engine = PVEngine(self.hz_spinbox)
        
    def connectWidgets(self):
        def togglePlay(play: bool):                   
            if play:
                self.engine.start()
            else:
                self.engine.stop()
        
        self.toggle_play_button.toggled.connect(togglePlay)
        self.engine.updateCanvas.connect(self.updateCanvasScript)
        
    def updateCanvasScript(self, time_step):
        PEN_WIDTH = 4
        
        self._times.append(self._times[-1] + time_step if self._times else 0)
        
        for item in self.pv_editor.table.getItems():
            if not item.isPVSet():
                continue
            
            data = item.fetchData()
            
            pv_data = data["PV"].get()
            times = self._times[-len(pv_data):]
                
            
            kwargs = deepcopy(data["kwargs"])  # enables use of `del` and `pop()` without affecting the item's data directly
            
            original_kwargs = kwargs.get("original", {})
            rw_kwargs = kwargs.get("rolling_window", {})
            ewm_kwargs = kwargs.get("ewm", {})
            aggregation_function = kwargs.get("aggregation_function", "mean")
            
            if original_kwargs.get("enabled", False):
                curve = self.canvas.getCurve(data["name"])
                
                pen = mkPen(color=data["color"], width=PEN_WIDTH)
                
                if curve:
                    self.canvas.updateCurve(data["name"], times, pv_data, pen, data["window_number"] - 1)
                else:
                    self.canvas.addCurve(data["name"], times, pv_data, pen, data["window_number"] - 1)
            
            elif self.canvas.isCurve(data["name"]):
                self.canvas.removeCurve(data["name"])
                    
            if rw_kwargs.get("enabled", False):
                del rw_kwargs["enabled"]
                
                rolling_average = pd.Series(pv_data).rolling(**rw_kwargs).agg(aggregation_function).tolist()
                
                label = data["name"] + " Rolling-Window"
                curve = self.canvas.getCurve(label)
                
                pen = mkPen(color=data["color"], width=PEN_WIDTH, style=Qt.PenStyle.DashLine)
                
                if curve:
                    self.canvas.updateCurve(label, times, rolling_average, pen, data["window_number"] - 1)
                else:
                    self.canvas.addCurve(label, times, rolling_average, pen, data["window_number"] - 1)
                    
            elif self.canvas.isCurve(data["name"] + " Rolling-Window"):
                self.canvas.removeCurve(data["name"] + " Rolling-Window")
                
            if ewm_kwargs.get("enabled", False):
                del ewm_kwargs["enabled"]
                
                ewm_average = pd.Series(pv_data).ewm(**ewm_kwargs).agg(aggregation_function).tolist()
                
                label = data["name"] + " Exponentially Weighted"
                curve = self.canvas.getCurve(label)
                
                pen = mkPen(color=data["color"], width=PEN_WIDTH, style=Qt.PenStyle.DotLine)
                
                if curve:
                    self.canvas.updateCurve(label, times, ewm_average, pen, data["window_number"] - 1)
                else:
                    self.canvas.addCurve(label, times, ewm_average, pen, data["window_number"] - 1)
            
            elif self.canvas.isCurve(data["name"] + " Exponentially Weighted"):
                self.canvas.removeCurve(data["name"] + " Exponentially Weighted")
                
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
