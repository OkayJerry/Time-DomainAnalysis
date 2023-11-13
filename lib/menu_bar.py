import os
import json

from PyQt6.QtWidgets import QMenuBar, QFileDialog, QMenu
from PyQt6.QtGui import QAction

from pandas import DataFrame, read_csv, read_json

SAMPLE_HEADER_EXTENSION = "_samples"
SAMPLE_TIME_HEADER_EXTENSION = "_sample_times"

class MenuBar(QMenuBar):
    def __init__(self, main_window):
        super().__init__()
                 
        self.main_window = main_window
        
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
        
        new_action.triggered.connect(self.main_window.reset)
        open_data_action.triggered.connect(self.onOpenData)
        open_params_action.triggered.connect(self.onOpenParameters)
        save_data_action.triggered.connect(self.onSaveData)
        save_params_action.triggered.connect(self.onSaveParameters)
        
        file_menu = self.addMenu("File")
        file_menu.addAction(new_action)
        file_menu.addMenu(open_menu)
        file_menu.addMenu(save_menu)
    
    def onOpenData(self):        
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Data File...", "", "All Files (*);;JSON Files (*.json);;CSV Files (*.csv)")
        _, file_extension = os.path.splitext(file_path)
        
        if file_path and (file_extension == ".json" or file_extension == ".csv"):
            with open(file_path, 'r') as file:
                if "json" in file_path:
                    data = read_json(file).to_dict(orient="list")
                else:
                    data = read_csv(file).to_dict(orient="list")
            
            self.main_window.reset()
            
            sample_map = {}
            times_map = {}
            for header, vals in data.items():
                if SAMPLE_HEADER_EXTENSION in header:
                    name = header.replace(SAMPLE_HEADER_EXTENSION, "")
                    sample_map[name] = vals
                else:
                    name = header.replace(SAMPLE_TIME_HEADER_EXTENSION, "")
                    times_map[name] = vals
                    
            for name in sample_map.keys():
                item = self.main_window.pv_editor.addItem()
                item.samples = sample_map[name]
                item.sample_times = times_map[name]
                item.updateParams({"name": name})
            
    def onOpenParameters(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON File...", "", "JSON Files (*.json);;All Files (*)")
        _, file_extension = os.path.splitext(file_path)
        
        if file_path and file_extension == ".json":
            with open(file_path, 'r') as file:
                pv_params = json.load(file)

            self.main_window.reset()
            
            for params in pv_params:
                item = self.main_window.pv_editor.addItem()
                item.updateParams(params)
    
    def onSaveData(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Data As...", "", "All Files (*);;JSON Files (*.json);;CSV Files (*.csv)")
        _, file_extension = os.path.splitext(file_path)
        
        if file_path and (file_extension == ".json" or file_extension == ".csv"):
            d = {}
            max_num_samples = 0
            
            for item in self.main_window.pv_editor:
                if not item.pv:
                    continue
                                
                if len(item.samples) > max_num_samples:
                    max_num_samples = len(item.samples)
                                
                d[item.params["name"] + SAMPLE_HEADER_EXTENSION] = item.samples
                d[item.params["name"] + SAMPLE_TIME_HEADER_EXTENSION] = item.sample_times
                
            for name in d.keys():
                d[name] = [None] * (max_num_samples - len(d[name])) + d[name]
                
            df = DataFrame(d)
            if file_extension == ".json":
                df.to_json(file_path, orient="records")
            else:
                df.to_csv(file_path, index=False)
            
    def onSaveParameters(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save JSON File As...", "", "JSON Files (*.json);;All Files (*)")
        _, file_extension = os.path.splitext(file_path)
    
        if file_path and file_extension == ".json":
            params = [item.params for item in self.main_window.pv_editor]
            json_data = json.dumps(params, indent=4)

            # Write the JSON data to a file
            with open(file_path, 'w') as file:
                file.write(json_data)
