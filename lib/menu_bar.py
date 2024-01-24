import os
import json
from datetime import datetime

from PyQt6.QtWidgets import QMenuBar, QFileDialog, QMenu
from PyQt6.QtGui import QAction

from pandas import DataFrame, read_csv, read_json

# Global constants for file extensions and headers
SAMPLE_HEADER_EXT = "_samples"
SAMPLE_TIME_HEADER_EXT = "_sample_times"
DEFAULT_SAVE_DATA_EXT = ".csv"
DEFAULT_SAVE_PARAMS_EXT = ".json"

class MenuBar(QMenuBar):
    """
    Custom menu bar for the main window.

    Attributes:
        main_window: Reference to the main window.

    Methods:
        __init__: Initializes the MenuBar with actions and menus.
        onFileOpenData: Handles the File>Open>Data action.
        onFileOpenParameters: Handles the File>Open>Parameters action.
        onFileSaveData: Handles the File>Save>Data action.
        onFileSaveParameters: Handles the File>Save>Parameters action.
    """
    def __init__(self, main_window):
        """
        Initializes a new MenuBar instance.

        Args:
            main_window: Reference to the main window.
        """
        super().__init__()
                 
        self.main_window = main_window
        
        # Create `File` menu actions and menus
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
        
        # Create `Edit` menu actions and menus
        clear_action = QAction("Clear Sample Histories", self)
        
        # Connect `File` actions to their respective slots
        new_action.triggered.connect(self.main_window.reset)
        open_data_action.triggered.connect(self.onFileOpenData)
        open_params_action.triggered.connect(self.onFileOpenParameters)
        save_data_action.triggered.connect(self.onFileSaveData)
        save_params_action.triggered.connect(self.onFileSaveParameters)
        
        # Connect `Edit` actions to their respective slots
        clear_action.triggered.connect(self.onClearAction)
        
        # Add `File` menus to the menu bar
        file_menu = self.addMenu("File")
        file_menu.addAction(new_action)
        file_menu.addMenu(open_menu)
        file_menu.addMenu(save_menu)
        
        # Add `Edit` menus to the menu bar
        edit_menu = self.addMenu("Edit")
        edit_menu.addAction(clear_action)
    
    def onFileOpenData(self):
        """
        Handles the "Open Data" action. Opens a file dialog to load data.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Data File...", "", "All Files (*);;JSON Files (*.json);;CSV Files (*.csv)")
        _, file_extension = os.path.splitext(file_path)
        
        # Check if a valid file path with allowed extension is selected
        if file_path and (file_extension == ".json" or file_extension == ".csv"):
            # Read data from the selected file based on its format
            with open(file_path, 'r') as file:
                if "json" in file_path:
                    data = read_json(file).to_dict(orient="list")
                else:
                    data = read_csv(file).to_dict(orient="list")
            
            # Reset the main window before loading new data
            self.main_window.reset()
            
            # Separate sample and time data
            sample_map = {}
            times_map = {}
            for header, vals in data.items():
                if SAMPLE_HEADER_EXT in header:
                    # Extract sample name and map to values
                    name = header.replace(SAMPLE_HEADER_EXT, "")
                    sample_map[name] = vals
                else:
                    # Extract sample time name and map to values
                    name = header.replace(SAMPLE_TIME_HEADER_EXT, "")
                    times_map[name] = vals
                    
            # Iterate through sample names and create PV items
            for name in sample_map.keys():
                # Add a new PVItem to the PV editor
                item = self.main_window.pv_editor.addItem()
                
                # Set sample and time data for the PVItem
                item.samples = sample_map[name]
                item.sample_times = times_map[name]
                
                # Update parameters for the PVItem
                item.updateParams({"name": name})
            
    def onFileOpenParameters(self):
        """
        Handles the "Open Parameters" action. Opens a file dialog to load parameter data.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON File...", "", "JSON Files (*.json);;All Files (*)")
        _, file_extension = os.path.splitext(file_path)
        
        # Check if a valid JSON file path is selected
        if file_path and file_extension == ".json":
            # Read PV parameters from the selected JSON file
            with open(file_path, 'r') as file:
                pv_params = json.load(file)

            # Reset the main window before loading new data
            self.main_window.reset()
            
            # Iterate through PV parameters and create PV items
            for params in pv_params:
                # Add a new PVItem to the PV editor
                item = self.main_window.pv_editor.addItem()
                
                # Update parameters for the PVItem based on the loaded data
                item.updateParams(params)
    
    def onFileSaveData(self):
        """
        Handles the "Save Data As" action. Opens a file dialog to save data.
        """
        now = datetime.now()
        file_path, _ = QFileDialog.getSaveFileName(self, 
                                                   "Save Data As...", 
                                                   f"TDA-data_{now.year}{now.month}{now.day}_{now.hour}{now.minute}{now.second}" + DEFAULT_SAVE_DATA_EXT, 
                                                   "All Files (*);;JSON Files (*.json);;CSV Files (*.csv)")
        _, file_extension = os.path.splitext(file_path)
        
        if not file_extension:
            file_extension = DEFAULT_SAVE_DATA_EXT
            
        # Check if a valid file path with either JSON or CSV extension is selected
        if file_path and (file_extension == ".json" or file_extension == ".csv"):
            # Initialize an empty dictionary to store data
            d = {}
            max_num_samples = 0
            
            # Iterate through PV items in the main window
            for item in self.main_window.pv_editor:
                # Skip items without associated PV data
                if not item.pv:
                    continue
                
                # Update the maximum number of samples
                if len(item.samples) > max_num_samples:
                    max_num_samples = len(item.samples)
                
                # Store sample data and corresponding sample times in the dictionary
                d[item.params["name"] + SAMPLE_HEADER_EXT] = item.samples
                d[item.params["name"] + SAMPLE_TIME_HEADER_EXT] = item.sample_times
            
            # Fill missing samples with `None` to ensure uniform data structure
            for name in d.keys():
                d[name] = [None] * (max_num_samples - len(d[name])) + d[name]
            
            # Create a DataFrame from the dictionary
            df = DataFrame(d)
            
            # Save the DataFrame to the selected file path based on the file extension
            if file_extension == ".json":
                df.to_json(file_path, orient="records")
            else:
                df.to_csv(file_path, index=False)
            
    def onFileSaveParameters(self):
        """
        Handles the "Save Parameters As" action. Opens a file dialog to save parameter data.
        """
        now = datetime.now()
        file_path, _ = QFileDialog.getSaveFileName(self,
                                                   "Save JSON File As...",
                                                   f"TDA-params_{now.year}{now.month}{now.day}_{now.hour}{now.minute}{now.second}" + DEFAULT_SAVE_PARAMS_EXT,
                                                   "JSON Files (*.json);;All Files (*)")
        _, file_extension = os.path.splitext(file_path)
    
        if not file_extension:
                file_extension = DEFAULT_SAVE_PARAMS_EXT
            
        # Check if a valid file path with a JSON extension is selected
        if file_path and file_extension == ".json":
            # Extract PV parameters from PV items in the main window
            params = [item.params for item in self.main_window.pv_editor]
            
            # Convert the parameters to JSON format with indentation
            json_data = json.dumps(params, indent=4)

            # Write the JSON data to the selected file path
            with open(file_path, 'w') as file:
                file.write(json_data)

    def onClearAction(self):
        for item in self.main_window.pv_editor:
            item.clearSamples()
            self.main_window.pv_editor.updated.emit()
