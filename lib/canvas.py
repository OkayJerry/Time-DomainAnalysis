import pyqtgraph as pg
from typing import List, Tuple

COLUMN_INDEX = 0

class Canvas(pg.GraphicsLayoutWidget):
    def __init__(self):
        super().__init__(show=True)
                
        self._curves = {}  # {label: pg.InfiniteLine}
        self._curve_parents = {}  # {label: pg.PlotItem}
        
    def addCurve(self, label: str, x: List[float], y: List[float], pen: pg.mkPen, subplot_id: int) -> pg.PlotDataItem:
        curve = pg.PlotDataItem(name=label, x=x, y=y)
        if subplot_id in self.ci.rows and self.ci.rows[subplot_id]:
            subplot = self.ci.rows[subplot_id][COLUMN_INDEX]
        else:
            subplot = self.addSubplot(subplot_id)
        
        curve.setPen(pen)
        
        subplot.addItem(curve, name=label)
        self._curves[label] = curve
        self._curve_parents[label] = subplot
                
        return curve
        
    def removeCurve(self, label: str) -> pg.PlotDataItem:
        assert label in self._curves and label in self._curve_parents, f"Curve entitled '{label}' could not be found."
        
        curve = self._curves[label]
        subplot = self._curve_parents[curve.name()]
        
        subplot.removeItem(curve)
        self._curves.pop(label)
        self._curve_parents.pop(label)
        
        if len(subplot.listDataItems()) == 0:
            self.removeItem(subplot)
                    
        return curve
        
    def isCurve(self, label: str) -> bool:
        return label in self._curves and label in self._curve_parents
            
    def addSubplot(self, subplot_id: int) -> pg.PlotItem:
        subplot = self.addPlot(row=subplot_id, col=COLUMN_INDEX, name=f"Subplot {subplot_id}",)
        subplot.setMouseEnabled(x=False, y=False)
        subplot.setAxisItems({"bottom": pg.DateAxisItem()})
        return subplot
        
    def moveCurve(self, label: str, dest_subplot_id: int) -> None:
        curve = self.removeCurve(label)
        if dest_subplot_id in self.ci.rows and self.ci.rows[dest_subplot_id]:
            subplot = self.ci.rows[dest_subplot_id][COLUMN_INDEX]
        else:
            subplot = self.addSubplot(dest_subplot_id)
        
        subplot.addItem(curve, name=label)
        self._curves[label] = curve
        self._curve_parents[label] = subplot
        
    def updateCurve(self, label: str, x: float = None, y: float = None, pen: pg.mkPen = None, subplot_id = None) -> pg.PlotDataItem:
        curve = self._curves[label]
        
        if x and y:
            curve.setData(x=x, y=y)
        
        if pen:
            curve.setPen(pen)
            
        if subplot_id is not None:
            subplot = self._curve_parents[label]
            if subplot.vb.name != f"Subplot {subplot_id}":
                self.moveCurve(label, subplot_id)
                        
    def getCurve(self, label: str) -> Tuple[List[float], List[float]]:
        """Returns tuple(x, y)."""
        if label in self._curves:
            curve = self._curves[label]
            x, y = curve.getData()
            return x.tolist(), y.tolist()
        return False
    
    def reset(self):
        self.clear()
        self._curves.clear()
        self._curve_parents.clear()