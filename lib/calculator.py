from copy import deepcopy

import numpy as np
import pandas as pd
from PyQt6.QtCore import QThread, pyqtSignal

from lib.pv_item import PVItem

# Global constant for aggregation function
AGG_FUNC = "mean"

def adaptive_average(waveR, phase_threshold=0.5, n_avg=8):
    """
    Compute the adaptive average of the input data.

    Args:
        waveR (array-like): The input data representing BPM phase error.
        phase_threshold (float, optional): The phase change threshold to disable averaging. Default is 0.5.
        n_avg (int, optional): The number of points to average over. Default is 8.

    Returns:
        waveA (ndarray): The adaptive average of the input data.
    """
    
    # Check if the input data is a numpy array
    if not isinstance(waveR, np.ndarray):
        waveR = np.array(waveR)

    if len(waveR) < 2:
        return np.array([])

    recentPts = [waveR[0]]
    waveA = np.zeros(len(waveR))

    for n in range(1, len(waveR)):
        newPts = np.append(recentPts, waveR[n])

        if len(newPts) > n_avg:
            newPts = newPts[1:(n_avg + 1)]

        waveA[n] = np.mean(newPts)

        # Check if phase change exceeds the threshold
        if abs(waveR[n] - waveA[n - 1]) > phase_threshold:
            waveA[n] = waveR[n]
            recentPts = [waveR[n]]
        else:
            recentPts = newPts

    return waveA


class Calculator(QThread):
    """
    A threaded calculator class for performing data processing operations on items in a PV editor.

    Attributes:
        calculatedRW (pyqtSignal): Signal emitted upon completion of rolling window calculation.
        calculatedEWM (pyqtSignal): Signal emitted upon completion of exponential weighted mean calculation.
        calculatedAA (pyqtSignal): Signal emitted upon completion of adaptive average calculation.

    Methods:
        __init__: Initializes the Calculator object with a PV editor.
        run: Overrides the run method of QThread; iterates over PV editor items, performs calculations, and emits signals.
    """
    calculatedRW = pyqtSignal(PVItem, list)
    calculatedEWM = pyqtSignal(PVItem, list)
    calculatedAA = pyqtSignal(PVItem, list)
    
    def __init__(self, pv_editor):
        """
        Initializes a new Calculator instance.

        Args:
            pv_editor (iterable): The PV editor containing items for calculation.
        """
        
        super().__init__()
        self.pv_editor = pv_editor
        
    def run(self):
        """
        Overrides the run method of QThread.
        Iterates over items in the PV editor, performs calculations, and emits signals.
        """
        
        for item in self.pv_editor:
            kwargs = deepcopy(item.params["kwargs"])  # Create a deep copy to avoid modifying the original data
            
            # Extract parameters for rolling window, exponential weighted mean, and adaptive average
            rw_kwargs = kwargs.get("rolling_window", {})
            ewm_kwargs = kwargs.get("ewm", {})
            aa_kwargs = kwargs.get("adaptive", {})
            
            # Check if rolling window is enabled
            if rw_kwargs.get("enabled", False):
                del rw_kwargs["enabled"]  # Remove the 'enabled' key to avoid interfering with the rolling function
                
                # Apply rolling window and emit the result signal
                rw_result = pd.Series(item.samples).rolling(**rw_kwargs).agg(AGG_FUNC).tolist()
                self.calculatedRW.emit(item, rw_result)
                
            # Check if exponential weighted mean is enabled
            if ewm_kwargs.get("enabled", False):
                del ewm_kwargs["enabled"]  # Remove the 'enabled' key
                
                # Apply exponential weighted mean and emit the result signal
                ewm_result = pd.Series(item.samples).ewm(**ewm_kwargs).agg(AGG_FUNC).tolist()
                self.calculatedEWM.emit(item, ewm_result)
                
            # Check if adaptive average is enabled
            if aa_kwargs.get("enabled", False):
                del aa_kwargs["enabled"]  # Remove the 'enabled' key
                
                # Apply adaptive average and emit the result signal
                aa_result = adaptive_average(item.samples, **aa_kwargs)
                self.calculatedAA.emit(item, aa_result)