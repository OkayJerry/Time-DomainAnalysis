from copy import deepcopy

from PyQt6.QtCore import pyqtSignal, QThread, Qt
from PyQt6.QtGui import QPen

from pyqtgraph import mkPen
import pandas as pd

from components.Canvas import DynamicCanvas
from components.PVEditor import PVTable
from components.Clock import Clock

PEN_WIDTH = 2

class PVProcessor(QThread):
    plotRequest = pyqtSignal(str, list, list, QPen, int)
    requestCurveRemoval = pyqtSignal(str)
    removeFlaggedItems = pyqtSignal()
    
    def __init__(self, table: PVTable, clock: Clock, canvas: DynamicCanvas):
        super().__init__()
        
        self.table = table
        self.clock = clock
        self.canvas = canvas
        self._times = []
    
    def run(self, draw=True):
        self._times.append(self._times[-1] + self.clock.interval() / 1000.0 if self._times else 0)
        
        for item in self.table.getItems():
            if not item:
                continue
            
            data = item.getData()
            
            if not data:
                continue
                        
            item.addValue()
            pv_data = item.getValues()
            times = self._times[-len(pv_data):]
                
            kwargs = deepcopy(data["kwargs"])  # enables use of `del` and `pop()` without affecting the item's data directly
            
            og_kwargs = kwargs.get("original", {})
            rw_kwargs = kwargs.get("rolling_window", {})
            ewm_kwargs = kwargs.get("ewm", {})
            aggregation_function = kwargs.get("aggregation_function", "mean")
            
            if og_kwargs.get("enabled", False) and not item.removal_flag and draw:
                del og_kwargs["enabled"]
                
                self.plotRequest.emit(data["label"], 
                                      times, 
                                      pv_data, 
                                      mkPen(color=data["color"], width=PEN_WIDTH), 
                                      data["window_number"] - 1)
                
            elif self.canvas.isCurve(data["label"]):
                self.requestCurveRemoval.emit(data["label"])
            
            if rw_kwargs.get("enabled", False) and not item.removal_flag and draw:
                del rw_kwargs["enabled"]
                
                rolling_average = pd.Series(pv_data).rolling(**rw_kwargs).agg(aggregation_function).tolist()
                self.plotRequest.emit(data["label"] + " Rolling-Window", 
                                      times, 
                                      rolling_average, 
                                      mkPen(color=data["color"], width=PEN_WIDTH, style=Qt.PenStyle.DashLine), 
                                      data["window_number"] - 1)
                
            elif self.canvas.isCurve(data["label"] + " Rolling-Window"):
                self.requestCurveRemoval.emit(data["label"] + " Rolling-Window")
                
            if ewm_kwargs.get("enabled", False) and not item.removal_flag and draw:
                del ewm_kwargs["enabled"]
                
                ewm_average = pd.Series(pv_data).ewm(**ewm_kwargs).agg(aggregation_function).tolist()
                self.plotRequest.emit(data["label"] + " Exponentially Weighted",
                                      times,
                                      ewm_average,
                                      mkPen(color=data["color"], width=PEN_WIDTH, style=Qt.PenStyle.DotLine),
                                      data["window_number"] - 1)
                
            elif self.canvas.isCurve(data["label"] + " Exponentially Weighted"):
                self.requestCurveRemoval.emit(data["label"] + " Exponentially Weighted")
                
        self.removeFlaggedItems.emit()
                
    def getTimes(self):
        return self._times
    
    def load(self, times):
        self._times = times