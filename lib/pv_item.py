import os
from time import time

from PyQt6.QtWidgets import (QWidget, QDoubleSpinBox, QComboBox, QRadioButton, QPushButton, 
                             QDialog, QSpinBox, QLabel, QColorDialog, QLineEdit, QMessageBox,
                             QTreeWidget, QTreeWidgetItem, QCheckBox, QHBoxLayout, QGridLayout, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QColor

from epics import PV

from lib.critical_dialog import CriticalDialog


PV_LABEL_PLACEHOLDER = "Insert PV Name"
PV_LABEL_ALIGNMENT = Qt.AlignmentFlag.AlignCenter
PV_PARAM_BUTTON_LABEL = "Parameters"
ITEM_LAYOUT_ALIGNMENT = Qt.AlignmentFlag.AlignVCenter
SPINBOX_ALIGNMENT = Qt.AlignmentFlag.AlignCenter
DEFAULT_COLOR = "#ffffff"  # white
DEFAULT_SUBPLOT_ID = 0
DEFAULT_KWARGS = {"original": {'enabled': True},
                  "rolling_window": {'enabled': False, 'window': 1, 'center': False, 'closed': 'right'},
                  "ewm": {'enabled': False, 'com': 0.0, 'span': None, 'halflife': None, 'alpha': None, 'adjust': False},
                  "adaptive": {'enabled': False, 'phase_threshold': 0.5, 'n_avg': 8}}
DIALOG_WIDTH = 350
DIALOG_MODALITY = True
DIALOG_ICON_FILENAME = os.path.join(os.getcwd(), "resources", "images", "frib.png")

class PVItem(QWidget):
    paramsChanged = pyqtSignal(dict)
    
    def __init__(self, pv_editor):
        super().__init__()
        
        self.pv_editor = pv_editor
        
        self.pv = None
        self.params = {"name": None,
                       "color": DEFAULT_COLOR,
                       "subplot_id": DEFAULT_SUBPLOT_ID,
                       "kwargs": DEFAULT_KWARGS}
        
        self.samples = []
        self.sample_times = []
        
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.line_edit = QLineEdit("")
        self.line_edit.setPlaceholderText(PV_LABEL_PLACEHOLDER)
        self.line_edit.setAlignment(PV_LABEL_ALIGNMENT)
        self.line_edit.returnPressed.connect(self.line_edit.clearFocus)
        self.line_edit.returnPressed.connect(lambda: self.updateParams({"name": self.line_edit.text()}))
        
        self.color_square = PaletteButton()
        self.color_square.setEnabled(False)  # button -> colored rectangle
        
        self.param_button = QPushButton(PV_PARAM_BUTTON_LABEL)
        self.param_button.pressed.connect(self._showParamDialog)
        
        self.param_dialog = ParameterDialog()
        self.param_dialog.apply_button.pressed.connect(self._onApplyParams)
        
        layout = QHBoxLayout()
        layout.setAlignment(ITEM_LAYOUT_ALIGNMENT)
        layout.addWidget(self.line_edit)
        self.setLayout(layout)
        
    def updateParams(self, params: dict = {}):
        try:
            if params.get("name", "") and params["name"] != self.params["name"]:
                # Verify the name isn't already taken
                for item in self.pv_editor:
                    if item is not self and item.params["name"] == params["name"]:
                        self.line_edit.setFocus()
                        self.line_edit.setText(self.params["name"] if self.params["name"] is not None else "")
                        raise ValueError(f"'{params['name']}' already exists...")
                
                self.pv = PV(params["name"])
                self.line_edit.setText(params["name"])
            
            self.params.update(params)
            
            name_was_set = "name" in self.params.keys() and self.params["name"] is not None
            only_line_edit_showing = self.layout().indexOf(self.color_square) == -1 and self.layout().indexOf(self.param_button) == -1
            if name_was_set and only_line_edit_showing:
                self.layout().addSpacing(10)
                self.layout().addWidget(self.color_square)
                self.layout().addWidget(self.param_button)
                
            self.color_square.setColor(self.params["color"])
            
            self.param_dialog.updateParams(self.params)
            
            self.paramsChanged.emit(self.params)
        except Exception as exc:
            critical_dialog = CriticalDialog(str(exc), self)
            critical_dialog.exec()
        
    def _showParamDialog(self):
        self.param_dialog.exec()
        
    def _onApplyParams(self):
        params = self.param_dialog.getParams()
        self.color_square.setColor(params["color"])
        self.params.update(params)
        
        self.paramsChanged.emit(self.params)
        
    def sample(self) -> float:
        sample = self.pv.get()
        self.sample_times.append(float(time()))
        self.samples.append(sample)
        return sample


class ParameterDialog(QDialog):
    def __init__(self):
        super().__init__()
                
        self.setWindowIcon(QIcon(DIALOG_ICON_FILENAME))
        self.setFixedWidth(DIALOG_WIDTH)
        self.setModal(DIALOG_MODALITY)
        
        self.tree = KwargTree()
        self.subplot_id_spinbox = QSpinBox()
        self.subplot_id_spinbox.setMinimum(1)
        self.subplot_id_spinbox.setAlignment(SPINBOX_ALIGNMENT)
        self.palette_button = PaletteButton()
        self.apply_button = QPushButton("Apply")
        
        self.apply_button.pressed.connect(self.accept)
        
        layout = QGridLayout()
        layout.addWidget(self.tree, 0, 0, 1, 2)
        layout.addWidget(QLabel("Subplot ID"), 1, 0, 1, 1)
        layout.addWidget(self.subplot_id_spinbox, 1, 1, 1, 1)
        layout.addWidget(QLabel("Color"), 2, 0, 1, 1)
        layout.addWidget(self.palette_button, 2, 1, 1, 1)
        layout.addWidget(self.apply_button, 3, 0, 1, 2)
        self.setLayout(layout)
        
    def getParams(self) -> dict:
        kwargs = self.tree.getKwargs()
        color = self.palette_button.color
        subplot_id = self.subplot_id_spinbox.value() - 1
        
        return {"kwargs": kwargs, "color": color, "subplot_id": subplot_id}
    
    def updateParams(self, params: dict):
        keys = params.keys()
            
        if "name" in keys and params["name"] is not None:
            self.setWindowTitle(f"{params['name']}'s Parameters")
            
        if "color" in keys:
            self.palette_button.setColor(params["color"])
            
        if "subplot_id" in keys:
            self.subplot_id_spinbox.setValue(params["subplot_id"])
            
        if "kwargs" in keys:
            self.tree.updateKwargs(params["kwargs"])
        
class KwargTree(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("QTreeWidget::item { height: 25px; }")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setColumnCount(2)
        self.setColumnWidth(0, 175)
        self.setHeaderHidden(True)
        self.setUniformRowHeights(True)

        # Original
        og_item = QTreeWidgetItem(self, ["Original"])
        og_item.setFirstColumnSpanned(True)
        og_enable_item = QTreeWidgetItem(og_item, ["Enable"])
        self.og_checkbox = QCheckBox()
        self.og_checkbox.setChecked(True)
        self.setItemWidget(og_enable_item, 1, self.og_checkbox)

        # Rolling-Window Average
        rw_item = QTreeWidgetItem(self, ["Rolling Window"])
        rw_item.setFirstColumnSpanned(True)
        rw_enable_item = QTreeWidgetItem(rw_item, ["Enable"])  # Enable
        self.rw_checkbox = QCheckBox()
        self.setItemWidget(rw_enable_item, 1, self.rw_checkbox)
        rw_window_item = QTreeWidgetItem(rw_item, ["Window"])  # Window Size
        rw_window_item.setToolTip(0, "Size of the moving window.")
        self.rw_window_spinbox = QSpinBox()
        self.rw_window_spinbox.setAlignment(SPINBOX_ALIGNMENT)
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

        # Exponentially-Weighted Means
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
        
        # Adaptive Average
        aa_item = QTreeWidgetItem(self, ["Adaptive Average"])
        aa_item.setFirstColumnSpanned(True)
        adaptive_enable_item = QTreeWidgetItem(aa_item, ["Enable"])  # Enable
        self.aa_checkbox = QCheckBox()
        self.setItemWidget(adaptive_enable_item, 1, self.aa_checkbox)
        adaptive_threshold_item = QTreeWidgetItem(aa_item, ["Phase Threshold"])  # Phase Threshold
        self.aa_threshold_spinbox = QDoubleSpinBox()
        self.aa_threshold_spinbox.setValue(0.5)
        self.aa_threshold_spinbox.setSingleStep(0.25)
        self.aa_threshold_spinbox.setToolTip("The phase change threshold to disable averaging.")
        self.setItemWidget(adaptive_threshold_item, 1, self.aa_threshold_spinbox)
        adaptive_threshold_item = QTreeWidgetItem(aa_item, ["Number of Points"])  # Num(points) to average
        self.aa_pnts_spinbox = QSpinBox()
        self.aa_pnts_spinbox.setAlignment(SPINBOX_ALIGNMENT)
        self.aa_pnts_spinbox.setMinimum(1)
        self.aa_pnts_spinbox.setValue(8)
        self.aa_pnts_spinbox.setToolTip("Number of points to consider in calculations.")
        self.setItemWidget(adaptive_threshold_item, 1, self.aa_pnts_spinbox)
        
        def disableEWMRadioButtons(parent: OptionalDoubleSpinBox):
            related_optional_spinboxes = [self.ewm_com_spinbox, self.ewm_span_spinbox,
                                  self.ewm_halflife_spinbox, self.ewm_alpha_spinbox]
            related_optional_spinboxes.remove(parent)
            
            if not parent.isEnabled():
                parent.setEnabled(True)
                return
                
            for optional_spinbox in related_optional_spinboxes:
                optional_spinbox.setEnabled(False)
            
        self.ewm_com_spinbox.setEnabled(True)
        self.ewm_com_spinbox.disableOtherRadioButtons.connect(lambda: disableEWMRadioButtons(self.ewm_com_spinbox))
        self.ewm_span_spinbox.disableOtherRadioButtons.connect(lambda: disableEWMRadioButtons(self.ewm_span_spinbox))
        self.ewm_halflife_spinbox.disableOtherRadioButtons.connect(lambda: disableEWMRadioButtons(self.ewm_halflife_spinbox))
        self.ewm_alpha_spinbox.disableOtherRadioButtons.connect(lambda: disableEWMRadioButtons(self.ewm_alpha_spinbox))   

    def getKwargs(self) -> dict:
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
        
        d["adaptive"] = {"enabled": self.aa_checkbox.isChecked(),
                         "phase_threshold": self.aa_threshold_spinbox.value(),
                         "n_avg": self.aa_pnts_spinbox.value()}
        
        return d
    
    def updateKwargs(self, kwargs: dict):
        og = kwargs.get("original", {})
        rw = kwargs.get("rolling_window", {})
        ewm = kwargs.get("ewm", {})
        aa = kwargs.get("adaptive", {})
        
        if "enabled" in og.keys():
            self.og_checkbox.setChecked(og["enabled"])
            
        rw_keys = rw.keys()
        if "enabled" in rw_keys:
            self.rw_checkbox.setChecked(rw["enabled"])
        if "window" in rw_keys:
            self.rw_window_spinbox.setValue(rw["window"])
        if "center" in rw_keys:
            self.rw_center_checkbox.setChecked(rw["center"])
        if "closed" in rw_keys:
            self.rw_closed_combobox.setCurrentText(rw["closed"].capitalize())
            
        ewm_keys = ewm.keys()
        if "enabled" in ewm_keys:
            self.ewm_checkbox.setChecked(ewm["enabled"])
        if "com" in ewm_keys:
            self.ewm_com_spinbox.setValue(ewm["com"])
            self.ewm_com_spinbox.setEnabled(False if ewm["com"] is None else True)
        if "span" in ewm_keys:
            self.ewm_span_spinbox.setValue(ewm["span"])
            self.ewm_span_spinbox.setEnabled(False if ewm["span"] is None else True)
        if "halflife" in ewm_keys:
            self.ewm_halflife_spinbox.setValue(ewm["halflife"])
            self.ewm_halflife_spinbox.setEnabled(False if ewm["halflife"] is None else True)
        if "alpha" in ewm_keys:
            self.ewm_alpha_spinbox.setValue(ewm["alpha"])
            self.ewm_alpha_spinbox.setEnabled(False if ewm["alpha"] is None else True)
        if "adjust" in ewm_keys:
            self.ewm_adjust_checkbox.setChecked(ewm["adjust"])
            
        aa_keys = aa.keys()
        if "enabled" in aa_keys:
            self.aa_checkbox.setChecked(aa["enabled"])
        if "phase_threshold" in aa_keys:
            self.aa_threshold_spinbox.setValue(aa["phase_threshold"])
        if "n_avg" in aa_keys:
            self.aa_pnts_spinbox.setValue(aa["n_avg"])
        
    
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
        self.radiobutton.clicked.connect(lambda: self.setEnabled(True))
        self.radiobutton.clicked.connect(lambda: self.disableOtherRadioButtons.emit())
        self.radiobutton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setAlignment(SPINBOX_ALIGNMENT)
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
        return self.spinbox.value() if self.isEnabled() else None
    
    def setValue(self, value):
        if isinstance(value, float):
            self.setEnabled(True)
            self.spinbox.setValue(value)
        elif value is None:
            self.setEnabled(False)
            
    def setEnabled(self, b: bool):
        self.radiobutton.setChecked(b)
        self.spinbox.setEnabled(b)
        
    def isEnabled(self) -> bool:
        return self.radiobutton.isChecked()

class PaletteButton(QPushButton):
    def __init__(self):
        super().__init__()
        self.setColor("")
        self.pressed.connect(self._showColorDialog)
        
    def setColor(self, color: str):
        self.color = color
        self.setStyleSheet(f"background-color: {color};")  # hex-code
        
    def _showColorDialog(self):
        color = QColorDialog.getColor(QColor(self.color))

        if color.isValid():
            self.setColor(color.name())