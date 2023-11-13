from copy import deepcopy

import numpy as np
import pandas as pd
from PyQt6.QtCore import QThread, pyqtSignal

from lib.pv_item import PVItem


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

        if abs(waveR[n] - waveA[n - 1]) > phase_threshold:
            waveA[n] = waveR[n]
            recentPts = [waveR[n]]
        else:
            recentPts = newPts

    return waveA


class Calculator(QThread):
    calculatedRW = pyqtSignal(PVItem, list)
    calculatedEWM = pyqtSignal(PVItem, list)
    calculatedAA = pyqtSignal(PVItem, list)
    
    def __init__(self, pv_editor):
        super().__init__()
        self.pv_editor = pv_editor
        
    def run(self):        
        for item in self.pv_editor:
            kwargs = deepcopy(item.params["kwargs"])  # so `del` will not affect the item's data directly
            rw_kwargs = kwargs.get("rolling_window", {})
            ewm_kwargs = kwargs.get("ewm", {})
            aa_kwargs = kwargs.get("adaptive", {})
            
            if rw_kwargs.get("enabled", False):
                del rw_kwargs["enabled"]
                
                rw_result = pd.Series(item.samples).rolling(**rw_kwargs).agg(AGG_FUNC).tolist()
                self.calculatedRW.emit(item, rw_result)
                
            if ewm_kwargs.get("enabled", False):
                del ewm_kwargs["enabled"]
                
                ewm_result = pd.Series(item.samples).ewm(**ewm_kwargs).agg(AGG_FUNC).tolist()
                self.calculatedEWM.emit(item, ewm_result)
                
            if aa_kwargs.get("enabled", False):
                del aa_kwargs["enabled"]
                
                aa_result = adaptive_average(item.samples, **aa_kwargs)
                self.calculatedAA.emit(item, aa_result)