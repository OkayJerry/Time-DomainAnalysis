import os

from PyQt6.QtWidgets import QMainWindow, QGridLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from pyqtgraph import mkPen

from lib.calculator import Calculator
from lib.canvas import Canvas
from lib.clock import Clock
from lib.menu_bar import MenuBar
from lib.pv_editor import PVEditor

WINDOW_TITLE = "Time-Domain Analysis"
WINDOW_ICON_FILE = os.path.join(os.getcwd(), "resources", "images", "frib.png")
COLUMN_ZERO_WIDTH = 450
PEN_WIDTH = 2

RW_EXTENSION = " Rolling-Window"
EWM_EXTENSION = " Exponentially Weighted"
AA_EXTENSION = " Adaptive Average"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(QIcon(WINDOW_ICON_FILE))
        self.setMenuBar(MenuBar(self))
        
        self.canvas = Canvas()
        self.pv_editor = PVEditor(self)
        self.calculator = Calculator(self.pv_editor)
        self.clock = Clock()
        
        
        layout = QGridLayout()
        layout.addWidget(self.clock, 0, 0)
        layout.addWidget(self.pv_editor, 1, 0)
        layout.addWidget(self.canvas, 0, 1, 2, 1)
        
        self.clock.setFixedWidth(COLUMN_ZERO_WIDTH)
        self.pv_editor.setFixedWidth(COLUMN_ZERO_WIDTH)
        
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(layout)
        
        self._createMainThreadScripts()
                
    def reset(self):
        self.pv_editor.reset()
        self.canvas.reset()
        self.clock.reset()
        
    def _createMainThreadScripts(self):
        def onClockTimeout():
            # Generate new samples & draw (if enabled)
            for item in self.pv_editor:
                if not item.pv:
                    continue
                
                item.sample()
                pen = mkPen(color=item.params["color"], width=PEN_WIDTH)
        
                draw_enabled = item.params.get("kwargs", {}).get("original", {}).get("enabled", False)
                
                if draw_enabled and self.canvas.isCurve(item.params["name"]):
                    self.canvas.updateCurve(item.params["name"], item.sample_times, item.samples, pen, item.params["subplot_id"])
                elif draw_enabled and not self.canvas.isCurve(item.params["name"]):
                    self.canvas.addCurve(item.params["name"], item.sample_times, item.samples, pen, item.params["subplot_id"])
                elif not draw_enabled and self.canvas.isCurve(item.params["name"]):
                    self.canvas.removeCurve(item.params["name"])
                
            # Canvas clean-up
            names = [item.params["name"] for item in self.pv_editor]
            for label in self.canvas.getCurveLabels():
                label = label.replace(RW_EXTENSION, "")
                label = label.replace(EWM_EXTENSION, "")
                label = label.replace(AA_EXTENSION, "")
                if label not in names:
                    self.canvas.removeCurve(label)
                    
                
            # Run the calculator
            if not self.calculator.isRunning():
                self.calculator.start()
                
        def onCalculatedRW(item, result):
            name = item.params["name"] + RW_EXTENSION
            pen = mkPen(color=item.params["color"], width=PEN_WIDTH, style=Qt.PenStyle.DashLine)
            if self.canvas.isCurve(name):
                self.canvas.updateCurve(name, item.sample_times, result, pen, item.params["subplot_id"])
            else:
                self.canvas.addCurve(name, item.sample_times, result, pen, item.params["subplot_id"])
        
        def onCalculatedEWM(item, result):
            name = item.params["name"] + EWM_EXTENSION
            pen = mkPen(color=item.params["color"], width=PEN_WIDTH, style=Qt.PenStyle.DotLine)
            if self.canvas.isCurve(name):
                self.canvas.updateCurve(name, item.sample_times, result, pen, item.params["subplot_id"])
            else:
                self.canvas.addCurve(name, item.sample_times, result, pen, item.params["subplot_id"])
        
        def onCalculatedAA(item, result):
            name = item.params["name"] + AA_EXTENSION
            pen = mkPen(color=item.params["color"], width=PEN_WIDTH, style=Qt.PenStyle.DashDotLine)
            if self.canvas.isCurve(name):
                self.canvas.updateCurve(name, item.sample_times, result, pen, item.params["subplot_id"])
            else:
                self.canvas.addCurve(name, item.sample_times, result, pen, item.params["subplot_id"])
                
        self.clock.timer.timeout.connect(onClockTimeout)
        self.calculator.calculatedRW.connect(onCalculatedRW)
        self.calculator.calculatedEWM.connect(onCalculatedEWM)
        self.calculator.calculatedAA.connect(onCalculatedAA)
        