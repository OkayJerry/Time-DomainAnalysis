import json

from PyQt6.QtWidgets import QMenuBar, QFileDialog, QMenu
from PyQt6.QtGui import QAction

from pandas import DataFrame, read_csv, read_json

class MenuBar(QMenuBar):
    def __init__(self, main_window):
        super().__init__()
                 
        self.main = main_window
        
        new_action = QAction("New", self)
        open_menu = QMenu("Open...", self)
        save_menu = QMenu("Save...", self)
        
        open_data_action = QAction("Data", self)
        open_params_action = QAction("Parameters", self)
        save_data_action = QAction("Data", self)
        save_params_action = QAction("Parameters", self)
        
        open_menu.addAction(open_data_action)
        open_menu.addAction(open_params_action)
        save_menu.addAction(save_data_action)
        save_menu.addAction(save_params_action)
        
        new_action.triggered.connect(lambda: self.onNew())
        open_data_action.triggered.connect(lambda: self.onOpenData())
        open_params_action.triggered.connect(lambda: self.onOpenParameters())
        save_data_action.triggered.connect(lambda: self.onSaveData())
        save_params_action.triggered.connect(lambda: self.onSaveParameters())
        
        file_menu = self.addMenu("File")
        file_menu.addAction(new_action)
        file_menu.addMenu(open_menu)
        file_menu.addMenu(save_menu)
        
    def onNew(self):
        self.main.terminateProcesses()
        self.main.initializeWidgets()
        self.main.connectWidgets()
    
    def onOpenData(self):        
        filename, _ = QFileDialog.getOpenFileName(self, "Open Data File...", "", "All Files (*);;JSON Files (*.json);;CSV Files (*.csv)")
        
        if filename and (".json" in filename or ".csv" in filename):
            with open(filename, 'r') as file:
                
                if "json" in filename:
                    pv_data = read_json(file).to_dict(orient="list")
                else:
                    pv_data = read_csv(file).to_dict(orient="list")
            
            self.onNew()
            self.main.pv_editor.table.setRowCount(0)
            
            times = pv_data.pop("time (s)") 
            self.main.processor.load(times)
                
            self.main.pv_editor.table.loadPVData(pv_data)
            
    def onOpenParameters(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open JSON File...", "", "JSON Files (*.json);;All Files (*)")
        
        if filename and ".json" in filename:
            with open(filename, 'r') as file:
                params = json.load(file)

            self.onNew()
            self.main.pv_editor.table.setRowCount(0)
    
            self.main.pv_editor.table.loadPVParameters(params)
    
    def onSaveData(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Data As...", "", "All Files (*)JSON Files (*.json);;CSV Files (*.csv)")
        
        if filename and (".json" in filename or ".csv" in filename):
            times = self.main.processor.getTimes()
            items = self.main.pv_editor.table.getItems()
            
            d = {}
            for item in items:
                pv_name = item.getPVName()
                
                if not pv_name:
                    continue
                
                values = item.getValues()
                
                # All values must be the same length for `DataFrame`
                values = [None] * (len(times) - len(values)) + values
                
                d[pv_name] = values
                
            d["time (s)"] = times
                
            if ".json" in filename:
                DataFrame(d).to_json(filename, orient="records")
            else:
                DataFrame(d).to_csv(filename, index=False)
            
    def onSaveParameters(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save JSON File As...", "", "JSON Files (*.json);;All Files (*)")
    
        if filename and ".json" in filename:
            pv_params = []
            
            items = self.main.pv_editor.table.getItems()
            for item in items:
                data = item.getData()
                if item.getPVName() and data:
                    pv_params.append(data)
                    
            # DataFrame(pv_params).to_json(filename)
            json_data = json.dumps(pv_params, indent=4)

            # Write the JSON data to a file
            with open(filename, 'w') as file:
                file.write(json_data)
