import pyqtgraph as pg
from typing import List, Tuple

# Global constant for the column index
COLUMN_INDEX = 0

class Canvas(pg.GraphicsLayoutWidget):
    """
    Custom canvas class based on PyQtGraph for plotting curves and managing subplots.

    Attributes:
        _curves (dict): Dictionary to store curves by label.
        _curve_parents (dict): Dictionary to store the parent subplot of each curve.

    Methods:
        __init__: Initializes the Canvas with an empty layout.
        addCurve: Adds a new curve to the canvas with specified label, data, and subplot ID.
        removeCurve: Removes a curve from the canvas by label.
        isCurve: Checks if a curve with a given label exists on the canvas.
        addSubplot: Adds a new subplot to the canvas.
        moveCurve: Moves a curve from its current subplot to a new subplot.
        updateCurve: Updates the data, pen, or subplot of an existing curve.
        getCurve: Retrieves the data (x, y) of a curve by label.
        reset: Clears the canvas and resets stored curves and subplots.
        getCurveLabels: Returns a list of labels for all existing curves.
    """
    
    def __init__(self):
        """
        Initializes a new Canvas instance.
        """
        super().__init__(show=True)
                
        self._curves = {}  # {label: pg.InfiniteLine}
        self._curve_parents = {}  # {label: pg.PlotItem}
        
    def addCurve(self, label: str, x: List[float], y: List[float], pen: pg.mkPen, subplot_id: int) -> pg.PlotDataItem:
        """
        Adds a new curve to the canvas with the specified label, data, pen, and subplot ID.

        Args:
            label (str): The label for the new curve.
            x (List[float]): The x-axis data points.
            y (List[float]): The y-axis data points.
            pen (pg.mkPen): The pen style for the curve.
            subplot_id (int): The ID of the subplot where the curve should be added.

        Returns:
            pg.PlotDataItem: The added curve.
        """
        # Create a new PlotDataItem with specified label, data, and pen
        curve = pg.PlotDataItem(name=label, x=x, y=y)
        
        # Check if the specified subplot exists, otherwise create a new one
        if subplot_id in self.ci.rows and self.ci.rows[subplot_id]:
            subplot = self.ci.rows[subplot_id][COLUMN_INDEX]
        else:
            subplot = self.addSubplot(subplot_id)
        
        # Set the pen style for the curve
        curve.setPen(pen)
        
        # Add the curve to the specified subplot
        subplot.addItem(curve, name=label)
        
        # Update internal dictionaries
        self._curves[label] = curve
        self._curve_parents[label] = subplot
                
        return curve
        
    def removeCurve(self, label: str) -> pg.PlotDataItem:
        """
        Removes a curve from the canvas by label.

        Args:
            label (str): The label of the curve to be removed.

        Returns:
            pg.PlotDataItem: The removed curve.
        """
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
        """
        Checks if a curve with a given label exists on the canvas.

        Args:
            label (str): The label of the curve to check.

        Returns:
            bool: True if the curve exists, False otherwise.
        """
        return label in self._curves and label in self._curve_parents
            
    def addSubplot(self, subplot_id: int) -> pg.PlotItem:
        """
        Adds a new subplot to the canvas.

        Args:
            subplot_id (int): The ID of the new subplot.

        Returns:
            pg.PlotItem: The added subplot.
        """
        subplot = self.addPlot(row=subplot_id, col=COLUMN_INDEX, name=f"Subplot {subplot_id}",)
        subplot.setMouseEnabled(x=False, y=False)
        subplot.setAxisItems({"bottom": pg.DateAxisItem()})
        return subplot
        
    def moveCurve(self, label: str, dest_subplot_id: int) -> None:
        """
        Moves a curve from its current subplot to a new subplot.

        Args:
            label (str): The label of the curve to be moved.
            dest_subplot_id (int): The ID of the destination subplot.
        """
        # Remove curve from its current subplot
        curve = self.removeCurve(label)
        
        # Check if the destination subplot already exists or create a new one
        if dest_subplot_id in self.ci.rows and self.ci.rows[dest_subplot_id]:
            subplot = self.ci.rows[dest_subplot_id][COLUMN_INDEX]
        else:
            subplot = self.addSubplot(dest_subplot_id)
        
        # Add the curve to the destination subplot
        subplot.addItem(curve, name=label)
        
        # Update internal dictionaries
        self._curves[label] = curve
        self._curve_parents[label] = subplot
        
    def updateCurve(self, label: str, x: float = None, y: float = None, pen: pg.mkPen = None, subplot_id = None) -> pg.PlotDataItem:
        """
        Updates the data, pen, or subplot of an existing curve.

        Args:
            label (str): The label of the curve to be updated.
            x (float): The new x-axis data point.
            y (float): The new y-axis data point.
            pen (pg.mkPen): The new pen style for the curve.
            subplot_id (int): The new ID of the subplot.

        Returns:
            pg.PlotDataItem: The updated curve.
        """
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
        """
        Retrieves the data (x, y) of a curve by label.

        Args:
            label (str): The label of the curve.

        Returns:
            Tuple[List[float], List[float]]: The data points of the curve.
        """
        if label in self._curves:
            curve = self._curves[label]
            x, y = curve.getData()
            return x.tolist(), y.tolist()
        return False
    
    def reset(self):
        """
        Clears the canvas and resets stored curves and subplots.
        """
        self.clear()
        self._curves.clear()
        self._curve_parents.clear()
        
    def getCurveLabels(self):
        """
        Returns a list of labels for all existing curves.

        Returns:
            List[str]: List of curve labels.
        """
        return list(self._curves.keys())