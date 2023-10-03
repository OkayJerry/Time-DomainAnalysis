from PyQt6.QtWidgets import QWidget, QMessageBox, QHBoxLayout, QComboBox, QSpinBox, QColorDialog, QLabel, QPushButton, QVBoxLayout, QCheckBox, QTableWidget, QTreeWidget, QTreeWidgetItem, QLineEdit, QHeaderView, QDialog, QGridLayout
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QColor
from components.buttons import TogglePlayButton
from components.spinbox import OptionalDoubleSpinBox
from epics import PV
import pandas as pd
        
class PaletteButton(QPushButton):
    def __init__(self, color):
        super().__init__()
        self.setColor(color)
        
    def setColor(self, color: str):
        self.color = color
        self.setStyleSheet(f"background-color: {color};")  # hex-code

class AdvancedSettingsDialog(QDialog):
    apply = pyqtSignal(dict)
    
    def __init__(self, color: str):
        super().__init__()

        
        self.setModal(True)

        self.tree = ControlTree()
        self.window_number_spinbox = QSpinBox()
        self.window_number_spinbox.setMinimum(1)
        self.palette_button = PaletteButton(color)
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

class PVTableItem(QWidget):
    def __init__(self, color: str):
        """color is  a hex-code"""
        super().__init__()
        self.current_pv = ""
        self.pv_set = False
        self.data = {'kwargs': {'original': {'enabled': True}, 
                               'rolling_window': {'enabled': False, 'window': 1, 'center': False, 'closed': 'right'}, 
                               'ewm': {'enabled': False, 'com': 0.0, 'span': None, 'halflife': None, 'alpha': None, 'adjust': False}},
                     'window_number': 1, 
                     'color': color}
        
        self.line_edit = QLineEdit(self.current_pv)
        self.line_edit.setPlaceholderText("Insert PV Name")
        self.line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.palette_button = PaletteButton(color)
        self.option_button = AdvancedSettingsButton(self)
        
        self.palette_button.setEnabled(False)
        self.palette_button.setVisible(False)
        self.option_button.setVisible(False)
        
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.line_edit)
        layout.addSpacing(9)
        layout.addWidget(self.palette_button)
        layout.addWidget(self.option_button)
        self.setLayout(layout)
        
        self.line_edit.returnPressed.connect(self.on_return_pressed)
        
    def on_return_pressed(self):
        self.line_edit.clearFocus()
        self.current_pv = self.line_edit.text()

        not_empty: bool = self.current_pv != ""
        self.palette_button.setVisible(not_empty)
        self.option_button.setVisible(not_empty)
        
        self.data["name"] = self.current_pv
        
        try:
            self.data["PV"] = PV(self.current_pv)
        except Exception as exc:
            # Show a critical error message box
            error_message = QMessageBox(self)
            error_message.setIcon(QMessageBox.Icon.Critical)
            error_message.setWindowTitle("Critical Error")
            error_message.setText("An error occurred:")
            error_message.setInformativeText(str(exc))
            error_message.exec()
        
        if "PV" in self.data.keys() and self.data["PV"]:
            self.pv_set = True
        else:
            self.pv_set = False
        
    def getColor(self) -> str:
        return self.palette_button.color
    
    def getPVName(self) -> str:
        return self.current_pv
    
    def update(self, data):
        for k,v in data.items():
            self.data[k] = v
        self.palette_button.setColor(data["color"])
        
    def fetchData(self):
        return self.data
    
    def isPVSet(self) -> bool:
        return self.pv_set
        

class AdvancedSettingsButton(QPushButton):
    def __init__(self, item: PVTableItem):
        super().__init__("Advanced")
        
        self.item = item
        self.clicked.connect(self.on_click)
        
        self.settings_dialog = AdvancedSettingsDialog(self.item.getColor())
        self.settings_dialog.apply.connect(self.item.update)
        
    def on_click(self):
        self.settings_dialog.setTitle(f"{self.item.getPVName()}: Advanced Settings")
        self.settings_dialog.exec()

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
        
class PVTable(QTableWidget):
    def __init__(self):
        super().__init__(1, 1)
        self.setRowCount(0)
        self.setShowGrid(False)
        self.horizontalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        self.addItem()
        
    def addItem(self, color = None):
        if color is None:
            TAB_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
            ROW_HEIGHT = 50
            
            unavailable_colors = []
            for row in range(self.rowCount()):
                item = self.cellWidget(row, 0)
                if item:
                    color = item.getColor()
                    if color in TAB_COLORS:
                        unavailable_colors.append(color)
                        
                        if set(unavailable_colors) == set(TAB_COLORS):
                            unavailable_colors.clear()
            
            for tab_color in TAB_COLORS:
                if tab_color not in unavailable_colors:
                    color = tab_color
                    break
        
        item = PVTableItem(color)
        item.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.insertRow(self.rowCount())
        self.setCellWidget(self.rowCount() - 1, 0, item)
        self.setRowHeight(self.rowCount() - 1, ROW_HEIGHT)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Backspace:
            selected_row = self.currentRow()
            self.removeRow(selected_row)
            
    def getItems(self) -> [PVTableItem]:
        return [self.cellWidget(row, 0) for row in range(self.rowCount())]
    

class PVEditor(QWidget):
    def __init__(self):
        super().__init__()
        
        self.add_button = QPushButton("+")
        self.table = PVTable()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.table)
        self.setLayout(layout)
        
        self.add_button.setFixedWidth(50)
        self.add_button.clicked.connect(lambda: self.table.addItem())

class CalculationWorkerThread(QThread):
    calculationsComplete = pyqtSignal(str, list)
    
    def __init__(self, label: str, data: list, calculation: str, **kwargs):
        """
        Calculations: 'rolling-window' or 'exp-weighted'
        """
        allowed_calculations = ["rolling-window", "exp-weighted"]
        assert calculation in allowed_calculations, "'{}' is invalid. Choose between 'rolling-window' and 'exp-weighted'."
        
        super().__init__()
        self.requested_calculation = calculation
        self.data = data
        self.kwargs = kwargs
            
    def run(self):
        if self.requested_calculation == "rolling-window":
            rolling_average = pd.Series(self.data).rolling(**self.kwargs).agg("mean")
            self.calculationsComplete.emit(rolling_average.tolist())
        elif self.requested_calculation == "exp-weighted":
            rolling_average = pd.Series(self.data).rolling(**self.kwargs).agg("mean")
            self.calculationsComplete.emit(rolling_average.tolist())
        
        
    
    