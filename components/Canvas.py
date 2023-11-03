import pyqtgraph as pg
from typing import List, Tuple

class DynamicCanvas(pg.GraphicsLayoutWidget):
    def __init__(self):
        super().__init__(show=True)
        
        self.COLUMN_INDEX = 0
        
        self._curves = {}  # {label: pg.InfiniteLine}
        self._curve_parents = {}  # {label: pg.PlotItem}
        
    def addCurve(self, label: str, x: List[float], y: List[float], pen: pg.mkPen, subplot_index: int) -> pg.PlotDataItem:
        curve = pg.PlotDataItem(name=label, x=x, y=y)
        if subplot_index in self.ci.rows and self.ci.rows[subplot_index]:
            subplot = self.ci.rows[subplot_index][self.COLUMN_INDEX]
        else:
            subplot = self.addSubplot(subplot_index)
        
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
        # for subplot in self.items():
        #     if isinstance(subplot, pg.PlotItem):
        #         # Iterate through the items (lines) in the subplot
        #         for item in subplot.items:
        #             if isinstance(item, pg.PlotDataItem) and item.name() == label:
        #                 print(f"Found line with name '{label}' in a subplot.")
        return label in self._curves and label in self._curve_parents
        # return False
            
    def addSubplot(self, subplot_index: int) -> pg.PlotItem:
        subplot = self.addPlot(row=subplot_index, col=self.COLUMN_INDEX, name=f"Subplot {subplot_index}",)
        subplot.setMouseEnabled(x=False, y=False)
        subplot.setAxisItems({"bottom": pg.DateAxisItem()})
        return subplot
        
    def moveCurve(self, label: str, subplot_index: int) -> None:
        curve = self.removeCurve(label)
        if subplot_index in self.ci.rows and self.ci.rows[subplot_index]:
            subplot = self.ci.rows[subplot_index][self.COLUMN_INDEX]
        else:
            subplot = self.addSubplot(subplot_index)
        
        subplot.addItem(curve, name=label)
        self._curves[label] = curve
        self._curve_parents[label] = subplot
        
    def updateCurve(self, label: str, x: float = None, y: float = None, pen: pg.mkPen = None, subplot_index = None) -> pg.PlotDataItem:
        curve = self._curves[label]
        
        if x and y:
            curve.setData(x=x, y=y)
        
        if pen:
            curve.setPen(pen)
            
        if subplot_index is not None:
            subplot = self._curve_parents[label]
            if subplot.vb.name != f"Subplot {subplot_index}":
                self.moveCurve(label, subplot_index)
                        
            
    def getCurve(self, label: str) -> Tuple[List[float], List[float]]:
        """Returns tuple(x, y)."""
        if label in self._curves:
            curve = self._curves[label]
            x, y = curve.getData()
            return x.tolist(), y.tolist()
        return False
    
    def empty(self):
        for label in self._curves.keys():
            self.removeCurve(label)