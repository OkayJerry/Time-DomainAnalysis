from PyQt6.QtWidgets import (QWidget, QDoubleSpinBox, QComboBox, QRadioButton, QPushButton, 
                             QDialog, QSpinBox, QLabel, QColorDialog, QLineEdit, QMessageBox, 
                             QTreeWidget, QTreeWidgetItem, QCheckBox, QHBoxLayout, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from epics import PV

class PaletteButton(QPushButton):
    def __init__(self, color):
        super().__init__()
        self.setColor(color)
        
    def setColor(self, color: str):
        self.color = color
        self.setStyleSheet(f"background-color: {color};")  # hex-code
        

class OptionalDoubleSpinBox(QWidget):
    disableOtherRadioButtons = pyqtSignal()
    
    def __init__(self, initial_value: float, step: float = 0.25, comparator=lambda value: 0 <= value <= float("Inf")):
        super().__init__()
        
        if not comparator(initial_value):
            raise ValueError(f"Initial value must be within bounds.")
        
        self.prev_value = initial_value
        self.comparator = comparator
        
        self.ERROR = 1e-5
        
        self.radiobutton = QRadioButton()
        self.radiobutton.clicked.connect(lambda: self.disableOtherRadioButtons.emit())
        
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setValue(initial_value)
        self.spinbox.setSingleStep(step)
        self.spinbox.valueChanged.connect(self.onValueChanged)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.radiobutton)
        layout.addWidget(self.spinbox)
        self.setLayout(layout)
        
    
    def onValueChanged(self, value: float) -> None:
        self.spinbox.blockSignals(True)
        if not self.comparator(value - self.ERROR) or not self.comparator(value + self.ERROR):
            self.spinbox.setValue(self.prev_value)
        self.spinbox.blockSignals(False)
        
        self.prev_value = self.spinbox.value()
        
    def value(self):
        return self.spinbox.value() if self.radiobutton.isChecked() else None
    
    def setValue(self, value: float):
        self.spinbox.setValue(value)

class AdvancedSettingsDialog(QDialog):
    apply = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        
        self.setModal(True)

        self.tree = ControlTree()
        self.window_number_spinbox = QSpinBox()
        self.window_number_spinbox.setMinimum(1)
        self.palette_button = PaletteButton("")
        self.apply_button = QPushButton("Apply")
        
        self.palette_button.clicked.connect(self.getColor)
        self.apply_button.clicked.connect(self.finished)

        layout = QGridLayout()
        layout.addWidget(self.tree, 0, 0, 1, 2)
        layout.addWidget(QLabel("Plot Into Window No."), 1, 0, 1, 1)
        layout.addWidget(self.window_number_spinbox, 1, 1, 1, 1)
        layout.addWidget(QLabel("Color"), 2, 0, 1, 1)
        layout.addWidget(self.palette_button, 2, 1, 1, 1)
        layout.addWidget(self.apply_button, 3, 0, 1, 2)
        self.setLayout(layout)
        
    def getColor(self):
        color = QColorDialog.getColor(QColor(self.palette_button.color))

        if color.isValid():
            self.palette_button.setColor(color.name())
            
    def finished(self):
        data = {}
        data["kwargs"] = self.tree.fetchData()
        data["window_number"] = self.window_number_spinbox.value()
        data["color"] = self.palette_button.color
        self.apply.emit(data)
        self.accept()
        
    def setTitle(self, title: str):
        self.setWindowTitle(title)
        
    def loadSettings(self, settings: dict):
        self.tree.loadData(settings.get("kwargs", {}))
        self.window_number_spinbox.setValue(settings.get("window_number", 1))
        self.palette_button.setColor(settings.get("color", ""))

class PVTableItem(QWidget):
    def __init__(self):
        """color is  a hex-code"""
        super().__init__()
        self.data = {}
        self.PV = None
        self.value_history = []
        self.removal_flag = False
                
        self.line_edit = QLineEdit("")
        self.line_edit.setPlaceholderText("Insert PV Name")
        self.line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.palette_button = PaletteButton("")
        self.settings_button = AdvancedSettingsButton(self)
        self.palette_button.setEnabled(False)
        self.palette_button.setVisible(False)
        self.settings_button.setVisible(False)
        
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.line_edit)
        layout.addSpacing(9)
        layout.addWidget(self.palette_button)
        layout.addWidget(self.settings_button)
        self.setLayout(layout)
        
        self.line_edit.returnPressed.connect(self.on_return_pressed)
        
    def on_return_pressed(self):
        self.line_edit.clearFocus()
        
        requested_pv_name = self.line_edit.text()
        blank_pv = requested_pv_name == ""
        
        if blank_pv:
            self.PV = None
            self.data = {}
            return
        
        try:
            if requested_pv_name in [item.getPVName() for item in self.parent().parent().getItems()]:
                raise ValueError(f"'{requested_pv_name}' already exists.")
            
            self.PV = PV(requested_pv_name)
            
        except Exception as exc:
            # Show a critical error message box
            error_message = QMessageBox(self)
            error_message.setIcon(QMessageBox.Icon.Critical)
            error_message.setWindowTitle("Critical Error")
            error_message.setText("An error occurred:")
            error_message.setInformativeText(str(exc))
            error_message.exec()
            return
        
        default_color = self.parent().parent().getNextColor()
        
        self.data = {"label": requested_pv_name,
                        "color": default_color,
            "kwargs": {"original": {'enabled': True},
                        "rolling_window": {'enabled': False, 'window': 1, 'center': False, 'closed': 'right'},
                        "ewm": {'enabled': False, 'com': 0.0, 'span': None, 'halflife': None, 'alpha': None, 'adjust': False}},
            "window_number": 1}
        
        self.palette_button.setColor(default_color)
        self.palette_button.setVisible(not blank_pv)
        self.settings_button.setVisible(not blank_pv)
        
    def getColor(self) -> str:
        return self.palette_button.color
    
    def getPVName(self) -> str:
        return self.data["label"] if self.data else None
    
    def update(self, data):
        for k,v in data.items():
            self.data[k] = v
        self.palette_button.setColor(data["color"])
        
    def getData(self):
        return self.data if self.PV else {}
    
    def isPVSet(self) -> bool:
        return True if self.PV else False
    
    def getValues(self):
        return self.value_history
    
    def addValue(self):
        self.value_history.append(self.PV.get())
        
    def loadPVData(self, name: str, values: list):
        color = self.parent().parent().getNextColor()
        self.PV = PV(name)
        self.line_edit.setText(name)
        self.value_history = values   
        self.data = {"label": name,
                     "color": color,
                     "kwargs": {"original": {'enabled': True},
                     "rolling_window": {'enabled': False, 'window': 1, 'center': False, 'closed': 'right'},
                     "ewm": {'enabled': False, 'com': 0.0, 'span': None, 'halflife': None, 'alpha': None, 'adjust': False}},
                     "window_number": 1}
        
        self.palette_button.setColor(color)
        self.palette_button.setVisible(True)
        self.settings_button.setVisible(True)
        
    def loadPVParameters(self, params: dict):
        
        self.PV = PV(params["label"])
        self.data = params
        self.line_edit.setText(params["label"])
        self.value_history = []
        
        self.palette_button.setColor(params["color"])
        self.palette_button.setVisible(True)
        self.settings_button.setVisible(True)
        
        self.settings_button.loadSettings(params)
        

class AdvancedSettingsButton(QPushButton):
    def __init__(self, item: PVTableItem):
        super().__init__("Advanced")
        
        self.item = item
        self.clicked.connect(self.on_click)
        
        self.settings_dialog = AdvancedSettingsDialog()
        self.settings_dialog.apply.connect(self.item.update)
        
    def on_click(self):
        self.settings_dialog.palette_button.setColor(self.item.getColor())
        self.settings_dialog.setTitle(f"{self.item.getPVName()}: Advanced Settings")
        self.settings_dialog.exec()
        
    def loadSettings(self, settings):
        self.settings_dialog.loadSettings(settings)

class ControlTree(QTreeWidget):    
    def __init__(self):
        super().__init__()
        self.setStyleSheet("QTreeWidget::item { height: 25px; }")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setColumnCount(2)
        self.setColumnWidth(0, 140)
        self.setHeaderHidden(True)
        self.setUniformRowHeights(True)
        self.create_items()

    def create_items(self):
        # Original
        og_item = QTreeWidgetItem(self, ["Original"])
        og_item.setFirstColumnSpanned(True)
        og_enable_item = QTreeWidgetItem(og_item, ["Enable"])
        self.og_checkbox = QCheckBox()
        self.og_checkbox.setChecked(True)
        self.setItemWidget(og_enable_item, 1, self.og_checkbox)

        # Rolling Window
        rw_item = QTreeWidgetItem(self, ["Rolling Window"])
        rw_item.setFirstColumnSpanned(True)
        rw_enable_item = QTreeWidgetItem(rw_item, ["Enable"])  # Enable
        self.rw_checkbox = QCheckBox()
        self.setItemWidget(rw_enable_item, 1, self.rw_checkbox)
        rw_window_item = QTreeWidgetItem(rw_item, ["Window"])  # Window Size
        rw_window_item.setToolTip(0, "Size of the moving window.")
        self.rw_window_spinbox = QSpinBox()
        self.rw_window_spinbox.setMinimum(1)
        self.rw_window_spinbox.setToolTip("≥1")
        self.setItemWidget(rw_window_item, 1, self.rw_window_spinbox)
        rw_center_item = QTreeWidgetItem(rw_item, ["Center"])  # Center
        rw_center_item.setToolTip(0, "True: Set the window labels as the center of the window index.\nFalse: Set the window labels as the right edge of the window index.")
        self.rw_center_checkbox = QCheckBox()
        self.setItemWidget(rw_center_item, 1, self.rw_center_checkbox)
        rw_closed_item = QTreeWidgetItem(rw_item, ["Closed"])  # Closed
        rw_closed_item.setToolTip(0, "Right: The first point in the window is excluded from calculations.\nLeft: The last point in the window is excluded from calculations.\nBoth: No points in the window are excluded from calculations.\nNeither: The first and last points in the window are excluded from calcuations.")
        self.rw_closed_combobox = QComboBox()
        self.rw_closed_combobox.addItems(["Right", "Left", "Both", "Neither"])
        self.setItemWidget(rw_closed_item, 1, self.rw_closed_combobox)

        # Exponentially Weighted
        ewm_item = QTreeWidgetItem(self, ["Exponentially Weighted"])
        ewm_item.setFirstColumnSpanned(True)
        ewm_enable_item = QTreeWidgetItem(ewm_item, ["Enable"])  # Enable
        self.ewm_checkbox = QCheckBox()
        self.setItemWidget(ewm_enable_item, 1, self.ewm_checkbox)
        ewm_com_item = QTreeWidgetItem(ewm_item, ["Com"])  # Com
        ewm_com_item.setToolTip(0, "Specify decay in terms of center mass.")
        self.ewm_com_spinbox = OptionalDoubleSpinBox(0, step=0.25)
        self.ewm_com_spinbox.spinbox.setToolTip("a = 1/(1+com), for com ≥ 0")
        self.setItemWidget(ewm_com_item, 1, self.ewm_com_spinbox)
        ewm_span_item = QTreeWidgetItem(ewm_item, ["Span"])  # Span
        ewm_span_item.setToolTip(0, "Specify decay in terms of span.")
        self.ewm_span_spinbox = OptionalDoubleSpinBox(1, step=0.25, comparator=lambda val: 1 <= val <= float("Inf"))
        self.ewm_span_spinbox.spinbox.setToolTip("a = 2/(span+1), for span ≥ 1")
        self.setItemWidget(ewm_span_item, 1, self.ewm_span_spinbox)
        ewm_halflife_item = QTreeWidgetItem(ewm_item, ["Half-Life"])  # Half-Life
        ewm_halflife_item.setToolTip(0, "Specify decay in terms of half-life.")
        self.ewm_halflife_spinbox = OptionalDoubleSpinBox(0.25, step=0.25, comparator=lambda val: 0 < val <= float("Inf"))
        self.ewm_halflife_spinbox.spinbox.setToolTip("a = 1-exp(-ln(2)/halflife), for halflife > 0")
        self.setItemWidget(ewm_halflife_item, 1, self.ewm_halflife_spinbox)
        ewm_alpha_item = QTreeWidgetItem(ewm_item, ["Alpha"])  # Alpha
        ewm_alpha_item.setToolTip(0, "Specify smoothing factor `a` directly.")
        self.ewm_alpha_spinbox = OptionalDoubleSpinBox(0.1, step=0.1, comparator=lambda val: 0 < val <= 1)
        self.ewm_alpha_spinbox.spinbox.setToolTip("0<a≤1")
        self.setItemWidget(ewm_alpha_item, 1, self.ewm_alpha_spinbox)
        ewm_adjust_item = QTreeWidgetItem(ewm_item, ["Adjust"])  # Adjust
        ewm_adjust_item.setToolTip(0, "True: Calculate using weights\nFalse: Calculate using recursion")
        self.ewm_adjust_checkbox = QCheckBox()
        self.setItemWidget(ewm_adjust_item, 1, self.ewm_adjust_checkbox)
        
        
        def disableEWMRadioButtons(parent: OptionalDoubleSpinBox):
            other_radiobuttons = [self.ewm_com_spinbox.radiobutton, self.ewm_span_spinbox.radiobutton,
                                  self.ewm_halflife_spinbox.radiobutton, self.ewm_alpha_spinbox.radiobutton]
            other_radiobuttons.remove(parent.radiobutton)
            
            if not parent.radiobutton.isChecked():
                parent.radiobutton.setChecked(True)
                return
                
            for radiobutton in other_radiobuttons:
                radiobutton.setChecked(False)
            
        self.ewm_com_spinbox.radiobutton.setChecked(True)
        self.ewm_com_spinbox.disableOtherRadioButtons.connect(lambda: disableEWMRadioButtons(self.ewm_com_spinbox))
        self.ewm_span_spinbox.disableOtherRadioButtons.connect(lambda: disableEWMRadioButtons(self.ewm_span_spinbox))
        self.ewm_halflife_spinbox.disableOtherRadioButtons.connect(lambda: disableEWMRadioButtons(self.ewm_halflife_spinbox))
        self.ewm_alpha_spinbox.disableOtherRadioButtons.connect(lambda: disableEWMRadioButtons(self.ewm_alpha_spinbox))        
        
    def fetchData(self) -> dict:
        d = {}
        
        d["original"] = {"enabled": self.og_checkbox.isChecked()}
        
        d["rolling_window"] = {"enabled": self.rw_checkbox.isChecked(),
                               "window": self.rw_window_spinbox.value(),
                               "center": self.rw_center_checkbox.isChecked(),
                               "closed": self.rw_closed_combobox.currentText().lower()}
        
        d["ewm"] = {"enabled": self.ewm_checkbox.isChecked(),
                    "com": self.ewm_com_spinbox.value(),
                    "span": self.ewm_span_spinbox.value(),
                    "halflife": self.ewm_halflife_spinbox.value(),
                    "alpha": self.ewm_alpha_spinbox.value(),
                    "adjust": self.ewm_adjust_checkbox.isChecked()}
        
        return d
    
    def loadData(self, data: dict):
        og_kwargs = data.get("original", {})
        rw_kwargs = data.get("rolling_window", {})
        ewm_kwargs = data.get("ewm", {})
        if og_kwargs:
            self.og_checkbox.setChecked(True if og_kwargs.get("enabled", {}) else False)
            
        if rw_kwargs:
            self.rw_checkbox.setChecked(True if rw_kwargs.get("enabled", {}) else False)
            self.rw_window_spinbox.setValue(rw_kwargs.get("window", 1))
            self.rw_center_checkbox.setChecked(rw_kwargs.get("center", False))
            self.rw_closed_combobox.setCurrentText(rw_kwargs.get("closed", "Right").capitalize())
            
        if ewm_kwargs:
            self.ewm_checkbox.setChecked(True if ewm_kwargs.get("enabled", {}) else False)
            if ewm_kwargs.get("com", 0) is not None:
                self.ewm_com_spinbox.setValue(ewm_kwargs.get("com", 0))
            if ewm_kwargs.get("span", 1) is not None:
                self.ewm_span_spinbox.setValue(ewm_kwargs.get("span", 1))
            if ewm_kwargs.get("halflife", 0.25) is not None:
                self.ewm_halflife_spinbox.setValue(ewm_kwargs.get("halflife", 0.25))
            if ewm_kwargs.get("alpha", 0.1) is not None:
                self.ewm_alpha_spinbox.setValue(ewm_kwargs.get("alpha", 0.1))
            self.ewm_adjust_checkbox.setChecked(ewm_kwargs.get("adjust", False))
