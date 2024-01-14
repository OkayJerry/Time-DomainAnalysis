import os

from PyQt6.QtWidgets import QMainWindow, QGridLayout, QWidget, QSlider
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from pyqtgraph import mkPen

from lib.calculator import Calculator
from lib.canvas import Canvas
from lib.clock import Clock
from lib.menu_bar import MenuBar
from lib.pv_editor import PVEditor
from lib.data_point_limiter import DataPointLimiter

# Global constants for the main window
WINDOW_TITLE = "Time-Domain Analysis"
WINDOW_ICON_FILE = os.path.join(os.getcwd(), "resources", "images", "frib.png")
COLUMN_ZERO_WIDTH = 450
PEN_WIDTH = 2
CLOCK_HEIGHT = 75
SLIDER_HEIGHT = 70

RW_EXTENSION = " Rolling-Window"
EWM_EXTENSION = " Exponentially Weighted"
AA_EXTENSION = " Adaptive Average"


class MainWindow(QMainWindow):
    """
    Main window for Time-Domain Analysis application.

    Attributes:
        canvas (Canvas): Instance of the Canvas widget for displaying curves.
        pv_editor (PVEditor): Instance of the PVEditor widget for managing PV items.
        calculator (Calculator): Instance of the Calculator for performing calculations.
        clock (Clock): Instance of the Clock widget for controlling updates.

    Methods:
        __init__: Initializes the MainWindow with layout and components.
        reset: Resets the state of PV editor, canvas, and clock to default values.
        _createMainThreadScripts: Creates main thread scripts for clock timeout and calculator signals.
    """
    def __init__(self):
        """
        Initializes a new MainWindow instance.
        """
        super().__init__()

        # Set window properties
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(QIcon(WINDOW_ICON_FILE))
        self.setMenuBar(MenuBar(self))
        
        # Create main components
        self.canvas = Canvas()
        self.pv_editor = PVEditor(self)
        self.data_pnt_limiter = DataPointLimiter()
        self.calculator = Calculator(self.pv_editor, self.data_pnt_limiter)
        self.clock = Clock()
        
        # Set up the layout
        layout = QGridLayout()
        layout.addWidget(self.clock, 0, 0)
        layout.addWidget(self.pv_editor, 1, 0, 2, 1)
        layout.addWidget(self.canvas, 0, 1, 2, 1)
        layout.addWidget(self.data_pnt_limiter, 2, 1, 1, 1)
        
        self.clock.setFixedSize(COLUMN_ZERO_WIDTH, CLOCK_HEIGHT)
        self.pv_editor.setFixedWidth(COLUMN_ZERO_WIDTH)
        self.data_pnt_limiter.setFixedHeight(SLIDER_HEIGHT)
        
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(layout)
        
        # Create and connect main thread scripts
        self._createMainThreadScripts()
                
    def reset(self):
        """
        Resets the state of PV editor, canvas, and clock to default values.
        """
        self.pv_editor.reset()
        self.canvas.reset()
        self.clock.reset()
        
    def _createMainThreadScripts(self):
        """
        Creates main thread scripts for clock timeout and calculator signals.

        This method defines functions for handling clock timeout and calculator signals, connecting them to the appropriate
        slots. It ensures the generation, drawing, and cleanup of samples in the PV editor's canvas. Additionally, it manages
        the updating or adding of curves on the canvas based on the draw settings of each PV item. The calculator signals
        trigger the plotting of calculated rolling window (RW), exponentially weighted moving average (EWM), and adaptive
        average (AA) curves.

        The method establishes connections between the signals of the clock, calculator, and the corresponding functions.
        """
        def updateCanvas(sample: bool = True):
            # Generate new samples & draw (if enabled)
            for item in self.pv_editor:
                if not item.pv:
                    continue
                
                if sample:
                    item.sample()
                    
                pen = mkPen(color=item.params["color"], width=PEN_WIDTH)
        
                draw_enabled = item.params.get("kwargs", {}).get("original", {}).get("enabled", False)
                
                sample_limit = self.data_pnt_limiter.getValue()
                samples = item.samples[-sample_limit:] if sample_limit and sample_limit < len(item.samples) else item.samples
                
                if draw_enabled and self.canvas.isCurve(item.params["name"]):
                    self.canvas.updateCurve(item.params["name"], item.sample_times[-len(samples):], samples, pen, item.params["subplot_id"])
                elif draw_enabled and not self.canvas.isCurve(item.params["name"]):
                    self.canvas.addCurve(item.params["name"], item.sample_times[-len(samples):], samples, pen, item.params["subplot_id"])
                elif not draw_enabled and self.canvas.isCurve(item.params["name"]):
                    self.canvas.removeCurve(item.params["name"])
                
            # Canvas clean-up
            names = [item.params["name"] for item in self.pv_editor]
            for label in self.canvas.getCurveLabels():
                label_temp = label.replace(RW_EXTENSION, "")
                label_temp = label_temp.replace(EWM_EXTENSION, "")
                label_temp = label_temp.replace(AA_EXTENSION, "")
                if label_temp not in names:
                    self.canvas.removeCurve(label)
                    
            # Run Calculator
            if not self.calculator.isRunning():
                self.calculator.start()
                
        def onCalculatedRW(item, result):
            """
            Callback function triggered on calculated rolling window (RW) signal from the calculator.

            This function handles the calculated RW data and updates the canvas with the appropriate pen settings.

            Args:
                item (PVItem): The PVItem for which the RW is calculated.
                result (List[float]): The calculated RW data.

            """
            name = item.params["name"] + RW_EXTENSION
            pen = mkPen(color=item.params["color"], width=PEN_WIDTH, style=Qt.PenStyle.DashLine)
            if self.canvas.isCurve(name):
                self.canvas.updateCurve(name, item.sample_times[-len(result):], result, pen, item.params["subplot_id"])
            else:
                self.canvas.addCurve(name, item.sample_times[-len(result):], result, pen, item.params["subplot_id"])
        
        def onCalculatedEWM(item, result):
            """
            Callback function triggered on calculated exponentially weighted moving average (EWM) signal from the calculator.

            This function handles the calculated EWM data and updates the canvas with the appropriate pen settings.

            Args:
                item (PVItem): The PVItem for which the EWM is calculated.
                result (List[float]): The calculated EWM data.

            """
            name = item.params["name"] + EWM_EXTENSION
            pen = mkPen(color=item.params["color"], width=PEN_WIDTH, style=Qt.PenStyle.DotLine)
            if self.canvas.isCurve(name):
                self.canvas.updateCurve(name, item.sample_times[-len(result):], result, pen, item.params["subplot_id"])
            else:
                self.canvas.addCurve(name, item.sample_times[-len(result):], result, pen, item.params["subplot_id"])
        
        def onCalculatedAA(item, result):
            """
            Callback function triggered on calculated adaptive average (AA) signal from the calculator.

            This function handles the calculated AA data and updates the canvas with the appropriate pen settings.

            Args:
                item (PVItem): The PVItem for which the AA is calculated.
                result (List[float]): The calculated AA data.

            """
            name = item.params["name"] + AA_EXTENSION
            pen = mkPen(color=item.params["color"], width=PEN_WIDTH, style=Qt.PenStyle.DashDotLine)
            if self.canvas.isCurve(name):
                self.canvas.updateCurve(name, item.sample_times[-len(result):], result, pen, item.params["subplot_id"])
            else:
                self.canvas.addCurve(name, item.sample_times[-len(result):], result, pen, item.params["subplot_id"])
            
        self.clock.timer.timeout.connect(updateCanvas)
        self.calculator.calculatedRW.connect(onCalculatedRW)
        self.calculator.calculatedEWM.connect(onCalculatedEWM)
        self.calculator.calculatedAA.connect(onCalculatedAA)
        self.pv_editor.updated.connect(lambda: updateCanvas(sample=False) if not self.clock.timer.isActive() else None)
        self.data_pnt_limiter.slider.valueChanged.connect(lambda: updateCanvas(sample=False) if not self.clock.timer.isActive() else None)