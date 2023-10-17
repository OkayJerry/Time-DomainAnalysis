import json

from PyQt6.QtWidgets import QMenuBar, QFileDialog, QMenu
from PyQt6.QtGui import QAction

from pandas import DataFrame

class MenuBar(QMenuBar):
    def __init__(self, main_window):
        super().__init__()
        
        # self.addMenu(FileMenu(main_window))
        
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
        filename, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json);;All Files (*)")
        
        if filename and ".json" in filename:
            with open(filename, 'r') as file:
                pv_data = json.load(file)
            
            self.onNew()
            self.main.pv_editor.table.setRowCount(0)
            
            times = sorted(pv_data.pop("time (s)").values())
            
            self.main.processor.load(times)
            self.main.pv_editor.table.loadPVData(pv_data)
            
    def onOpenParameters(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json);;All Files (*)")
        
        if filename and ".json" in filename:
            with open(filename, 'r') as file:
                params = json.load(file)

            self.onNew()
            self.main.pv_editor.table.setRowCount(0)
    
            self.main.pv_editor.table.loadPVParameters(params)
    
    def onSaveData(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save JSON File", "", "JSON Files (*.json);;All Files (*)")
        
        if filename and ".json" in filename:
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
                
            DataFrame(d).to_json(filename)
            
    def onSaveParameters(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save JSON File", "", "JSON Files (*.json);;All Files (*)")
    
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

                        
                
            
        

# class FileMenu(QMenu):
#     def __init__(self, main_window):
#         super().__init__("File")
        
#         self.main = main_window
        
#         new_action = QAction("New", self)
#         open_action = QAction("Open", self)
#         save_action = QAction("Save", self)
        
#         new_action.triggered.connect(lambda: self.onNew())
#         open_action.triggered.connect(lambda: self.onOpen)
#         save_action.triggered.connect(lambda: self.onSave)
        
#         self.addAction(new_action)
#         self.addAction(open_action)
#         self.addAction(save_action)
        
#     def onNew(self):
#         print("New started...")
#         self.main.canvas.clear()
#         self.main.initializeWidgets()
#         self.main.connectWidgets()
#         print("New finished...")
    
#     def onOpen(self):
#         print("Open Triggered")
    
#     def onSave(self):
#         print("Save Triggered")