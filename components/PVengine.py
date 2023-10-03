from epics import PV
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from threading import Thread
from time import sleep
import pandas as pd
from copy import deepcopy
from components.tools import PVTable
from components.DynamicCanvas import DynamicCanvas
from typing import List, Tuple

class PVWorkerThread(QThread):
    updateCanvas = pyqtSignal(float)
    
    def __init__(self, pv_engine, hz_spinbox):
        super().__init__()
        self.pv_engine = pv_engine
        self.hz_spinbox = hz_spinbox
                
    def run(self):
        while self.pv_engine.running:
            time_step = 1 / self.hz_spinbox.value()
            
            self.updateCanvas.emit(time_step)
                
            sleep(time_step)
        
class PVEngine(QObject):
    updateCanvas = pyqtSignal(float)
    
    def __init__(self, hz_spinbox):
        super().__init__()
        self.worker_thread = PVWorkerThread(self, hz_spinbox)
        self.running = False
        
        self.worker_thread.updateCanvas.connect(lambda time_step: self.updateCanvas.emit(time_step))
        
    def start(self):
        self.running = True
        self.worker_thread.start()
        
    def stop(self):
        self.running = False
        self.worker_thread.quit()
        
