import os
from copy import deepcopy
from time import time

from PyQt6.QtWidgets import (QWidget, QDoubleSpinBox, QComboBox, QRadioButton, QPushButton, 
                             QDialog, QSpinBox, QLabel, QColorDialog, QLineEdit, QMessageBox,
                             QTreeWidget, QTreeWidgetItem, QCheckBox, QHBoxLayout, QGridLayout, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QColor, QFontMetrics

from epics import PV

from lib.critical_dialog import CriticalDialog

# Constants and defaults
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
DIALOG_MODALITY = False
DIALOG_ICON_FILENAME = os.path.join(os.getcwd(), "resources", "images", "frib.png")
PV_VALUE_LABEL_TEXT_SIZE = 8
PV_VALUE_LABEL_GEOMETRY = (220, -1, 15)  # (x, y, height)
PARAM_BUTTON_WIDTH = 100
COLOR_SQUARE_WIDTH = 50


class PVItem(QWidget):
    """
    This class represents a widget for handling a PV (Process Variable) in a PV editor.

    Methods:
        updateParams: Update the PV parameters and trigger a signal for changes.
        _showParamDialog: Show the parameter dialog for the PV.
        _onApplyParams: Apply the changes made in the parameter dialog.
        sample: Sample the current value of the PV.

    Signals:
        paramsChanged: Signal emitted when the PV parameters are changed.

    Attributes:
        pv_editor: Reference to the parent PV editor.
        pv: The PV object associated with this widget.
        params: Dictionary containing PV parameters (name, color, subplot_id, kwargs).
        samples: List of sampled values from the PV.
        sample_times: List of corresponding sample times.

    Widgets:
        line_edit: QLineEdit for editing the PV name.
        color_square: PaletteButton for selecting the color of the PV curve.
        param_button: QPushButton for opening the parameter dialog.
        param_dialog: ParameterDialog for configuring advanced PV settings.

    Layout:
        The widget has a QHBoxLayout to arrange its child widgets.
    """
    paramsChanged = pyqtSignal(dict)
    
    def __init__(self, pv_editor):
        """
        Initializes a new PVItem instance.

        Args:
        - pv_editor: Reference to the parent PV editor.
        """
        super().__init__()
        
        self.pv_editor = pv_editor
        
        # Initialize PV-related attributes
        self.pv = None
        self.params = {"name": None,
                       "color": DEFAULT_COLOR,
                       "subplot_id": DEFAULT_SUBPLOT_ID,
                       "kwargs": DEFAULT_KWARGS}
        
        self.samples = []
        self.sample_times = []
        
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setContentsMargins(0, 0, 0, 0)
        
        # Set up PV name editing
        self.line_edit = QLineEdit("")
        self.line_edit.setPlaceholderText(PV_LABEL_PLACEHOLDER)
        self.line_edit.setAlignment(PV_LABEL_ALIGNMENT)
        self.line_edit.returnPressed.connect(self.line_edit.clearFocus)
        self.line_edit.returnPressed.connect(lambda: self.updateParams({"name": self.line_edit.text()}))
        
        # Set up PV color selection
        self.color_square = PaletteButton()
        self.color_square.setEnabled(False)  # button -> colored rectangle
        self.color_square.setFixedWidth(COLOR_SQUARE_WIDTH)
        
        # Set up PV parameter dialog
        self.param_button = QPushButton(PV_PARAM_BUTTON_LABEL)
        self.param_button.pressed.connect(self._showParamDialog)
        self.param_button.setFixedWidth(PARAM_BUTTON_WIDTH)
        self.param_dialog = ParameterDialog()
        self.param_dialog.apply_button.pressed.connect(self._onApplyParams)
        self.param_dialog.apply_ok_button.pressed.connect(self._onApplyParams)
        
        # Set up PV value display
        self.value_display = QLabel("", self)
        font = self.value_display.font()
        font.setPointSize(PV_VALUE_LABEL_TEXT_SIZE)
        self.value_display.setFont(font)
        self.value_display.setVisible(False)
        
        # Set up layout
        layout = QHBoxLayout()
        layout.setAlignment(ITEM_LAYOUT_ALIGNMENT)
        layout.addWidget(self.line_edit)
        self.setLayout(layout)
        
    def updateParams(self, params: dict = {}):
        """
        Update the PV parameters and trigger a signal for changes.

        Args:
            params (dict): Dictionary containing PV parameters to update.

        Raises:
            ValueError: Raised if the new PV name already exists in the PV editor.

        Signals:
            paramsChanged: Signal emitted when the PV parameters are changed.
        """
        try:
            # Check if the PV name has changed
            if params.get("name", "") and params["name"] != self.params["name"]:
                # Verify the name isn't already taken
                for item in self.pv_editor:
                    if item is not self and item.params["name"] == params["name"]:
                        self.line_edit.setFocus()
                        self.line_edit.setText(self.params["name"] if self.params["name"] is not None else "")
                        raise ValueError(f"'{params['name']}' already exists...")
                
                # Update the PV object with the new name
                self.pv = PV(params["name"])
                self.line_edit.setText(params["name"])
            
            # Update the PV parameters
            self.params.update(params)
            
            # Check if the PV name is set and only the line edit is showing
            name_was_set = "name" in self.params.keys() and self.params["name"] is not None
            only_line_edit_showing = self.layout().indexOf(self.color_square) == -1 and self.layout().indexOf(self.param_button) == -1
            if name_was_set and only_line_edit_showing:
                self.value_display.setVisible(True)
                self.layout().addSpacing(10)
                self.layout().addWidget(self.color_square)
                self.layout().addWidget(self.param_button)
                
                
            # Update the color square and parameter dialog
            self.color_square.setColor(self.params["color"])
            self.param_dialog.updateParams(self.params)
            
            # Emit the paramsChanged signal
            self.paramsChanged.emit(self.params)
            
        except Exception as exc:
            # Display a critical dialog in case of an exception
            critical_dialog = CriticalDialog(str(exc), self)
            critical_dialog.exec()
        
    def _showParamDialog(self):
        """
        Shows the parameter dialog for the PV item.
        """
        self.param_dialog.updateParams(self.params)
        self.param_dialog.show()
        
    def _onApplyParams(self):
        """
        Applies the changes made in the parameter dialog.
        """
        params = self.param_dialog.getParams()
        self.color_square.setColor(params["color"])
        self.params.update(params)
        
        self.paramsChanged.emit(self.params)
        
    def sample(self) -> float:
        """
        Samples the PV value and records sample time.

        Returns:
            float: Sampled PV value.
        """
        sample = self.pv.get()
        self.sample_times.append(float(time()))
        self.samples.append(sample)
        
        sample_text = "{:.3e}".format(sample)
        font_metrics = QFontMetrics(self.value_display.font())
        text_width = font_metrics.horizontalAdvance(sample_text)
        self.value_display.setGeometry(PV_VALUE_LABEL_GEOMETRY[0] - text_width, PV_VALUE_LABEL_GEOMETRY[1], 
                                       text_width, PV_VALUE_LABEL_GEOMETRY[2])
        self.value_display.setText(sample_text)
        
        return sample


class ParameterDialog(QDialog):
    """
    Dialog for editing parameters of a PVItem.

    Methods:
        __init__: Initializes a new ParameterDialog instance.
        getParams: Returns the edited parameters.
        updateParams: Updates the dialog with the given parameters.
        
    Attributes:
        tree (KwargTree): A widget for configuring PV parameters.
        subplot_id_spinbox (QSpinBox): A spin box for selecting the subplot ID.
        palette_button (PaletteButton): A button for choosing the PV color.
        apply_button (QPushButton): A button for applying changes.
        apply_ok_button (QPushButton): A button for applying changes and closing the window.
    """
    def __init__(self):
        """
        Initializes a new ParameterDialog instance.
        """
        super().__init__()
        
        # Set dialog properties
        self.setWindowIcon(QIcon(DIALOG_ICON_FILENAME))
        self.setFixedWidth(DIALOG_WIDTH)
        self.setModal(DIALOG_MODALITY)
        
        # Initialize widgets
        self.tree = KwargTree()
        self.subplot_id_spinbox = QSpinBox()
        self.subplot_id_spinbox.setMinimum(1)
        self.subplot_id_spinbox.setAlignment(SPINBOX_ALIGNMENT)
        self.palette_button = PaletteButton()
        self.apply_button = QPushButton("Apply")
        self.apply_ok_button = QPushButton("Apply && OK")
        
        # Connect the apply_ok_button to the accept method
        self.apply_ok_button.pressed.connect(self.accept)
        
        # Set up the layout
        layout = QGridLayout()
        layout.addWidget(self.tree, 0, 0, 1, 2)
        layout.addWidget(QLabel("Subplot ID"), 1, 0, 1, 1)
        layout.addWidget(self.subplot_id_spinbox, 1, 1, 1, 1)
        layout.addWidget(QLabel("Color"), 2, 0, 1, 1)
        layout.addWidget(self.palette_button, 2, 1, 1, 1)
        layout.addWidget(self.apply_button, 3, 0, 1, 1)
        layout.addWidget(self.apply_ok_button, 3, 1, 1, 1)
        self.setLayout(layout)
        
    def getParams(self) -> dict:
        """
        Returns the edited parameters.

        Returns:
            dict: Edited parameters.
        """
        kwargs = self.tree.getKwargs()
        color = self.palette_button.color
        subplot_id = self.subplot_id_spinbox.value() - 1
        
        return {"kwargs": kwargs, "color": color, "subplot_id": subplot_id}
    
    def updateParams(self, params: dict):
        """
        Updates the dialog with the given parameters.

        Args:
            params: Dictionary containing parameter updates.
        """
        keys = params.keys()
            
        if "name" in keys and params["name"] is not None:
            self.setWindowTitle(f"{params['name']}'s Parameters")
            
        if "color" in keys:
            self.palette_button.setColor(params["color"])
            
        if "subplot_id" in keys:
            self.subplot_id_spinbox.setValue(params["subplot_id"] + 1)
            
        if "kwargs" in keys:
            self.tree.updateKwargs(params["kwargs"])
        
class KwargTree(QTreeWidget):
    """
    Widget for displaying and editing parameters in a tree structure.

    Methods:
        __init__: Initializes a new KwargTree instance.
        getKwargs: Returns the edited parameters.
        updateKwargs: Updates the tree with the given parameters.
    """
    def __init__(self):
        """
        Initializes a new KwargTree instance.
        """
        super().__init__()
        self.setStyleSheet("QTreeWidget::item { height: 25px; }")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setColumnCount(2)
        self.setColumnWidth(0, 175)
        self.setHeaderHidden(True)
        self.setUniformRowHeights(True)

        # ------------ Original ------------
        og_item = QTreeWidgetItem(self, ["Original"])
        og_item.setFirstColumnSpanned(True)
        
        # Enable item for the "Original" section.
        og_enable_item = QTreeWidgetItem(og_item, ["Enable"])
        self.og_checkbox = QCheckBox()
        self.og_checkbox.setChecked(True)
        self.setItemWidget(og_enable_item, 1, self.og_checkbox)

        # ------------ Rolling-Window Average ------------
        rw_item = QTreeWidgetItem(self, ["Rolling Window"])
        rw_item.setFirstColumnSpanned(True)
        
        # Enable item for the "Rolling Window" section.
        rw_enable_item = QTreeWidgetItem(rw_item, ["Enable"])
        self.rw_checkbox = QCheckBox()
        self.setItemWidget(rw_enable_item, 1, self.rw_checkbox)
        
        # Window Size item for the "Rolling Window" section.
        rw_window_item = QTreeWidgetItem(rw_item, ["Window"])
        rw_window_item.setToolTip(0, "Size of the moving window.")
        self.rw_window_spinbox = QSpinBox()
        self.rw_window_spinbox.setAlignment(SPINBOX_ALIGNMENT)
        self.rw_window_spinbox.setMinimum(1)
        self.rw_window_spinbox.setToolTip("≥1")
        self.setItemWidget(rw_window_item, 1, self.rw_window_spinbox)
        
        # Center item for the "Rolling Window" section.
        rw_center_item = QTreeWidgetItem(rw_item, ["Center"])
        rw_center_item.setToolTip(0, "True: Set the window labels as the center of the window index.\nFalse: Set the window labels as the right edge of the window index.")
        self.rw_center_checkbox = QCheckBox()
        self.setItemWidget(rw_center_item, 1, self.rw_center_checkbox)
        
        # Closed item for the "Rolling Window" section.
        rw_closed_item = QTreeWidgetItem(rw_item, ["Closed"])
        rw_closed_item.setToolTip(0, "Right: The first point in the window is excluded from calculations.\nLeft: The last point in the window is excluded from calculations.\nBoth: No points in the window are excluded from calculations.\nNeither: The first and last points in the window are excluded from calcuations.")
        self.rw_closed_combobox = QComboBox()
        self.rw_closed_combobox.addItems(["Right", "Left", "Both", "Neither"])
        self.setItemWidget(rw_closed_item, 1, self.rw_closed_combobox)

        # ------------ Exponentially-Weighted Means ------------
        ewm_item = QTreeWidgetItem(self, ["Exponentially Weighted"])
        ewm_item.setFirstColumnSpanned(True)
        
        # Enable item for the "Exponentially Weighted" section.
        ewm_enable_item = QTreeWidgetItem(ewm_item, ["Enable"])
        self.ewm_checkbox = QCheckBox()
        self.setItemWidget(ewm_enable_item, 1, self.ewm_checkbox)
        
        # Com item for the "Exponentially Weighted" section.
        ewm_com_item = QTreeWidgetItem(ewm_item, ["Com"])
        ewm_com_item.setToolTip(0, "Specify decay in terms of center mass.")
        self.ewm_com_spinbox = OptionalDoubleSpinBox(0, step=0.25)
        self.ewm_com_spinbox.spinbox.setToolTip("a = 1/(1+com), for com ≥ 0")
        self.setItemWidget(ewm_com_item, 1, self.ewm_com_spinbox)
        
        # Span item for the "Exponentially Weighted" section.
        ewm_span_item = QTreeWidgetItem(ewm_item, ["Span"])
        ewm_span_item.setToolTip(0, "Specify decay in terms of span.")
        self.ewm_span_spinbox = OptionalDoubleSpinBox(1, step=0.25, comparator=lambda val: 1 <= val <= float("Inf"))
        self.ewm_span_spinbox.spinbox.setToolTip("a = 2/(span+1), for span ≥ 1")
        self.setItemWidget(ewm_span_item, 1, self.ewm_span_spinbox)
        
        # Half-Life item for the "Exponentially Weighted" section.
        ewm_halflife_item = QTreeWidgetItem(ewm_item, ["Half-Life"])
        ewm_halflife_item.setToolTip(0, "Specify decay in terms of half-life.")
        self.ewm_halflife_spinbox = OptionalDoubleSpinBox(0.25, step=0.25, comparator=lambda val: 0 < val <= float("Inf"))
        self.ewm_halflife_spinbox.spinbox.setToolTip("a = 1-exp(-ln(2)/halflife), for halflife > 0")
        self.setItemWidget(ewm_halflife_item, 1, self.ewm_halflife_spinbox)
        
        # Alpha item for the "Exponentially Weighted" section.
        ewm_alpha_item = QTreeWidgetItem(ewm_item, ["Alpha"])
        ewm_alpha_item.setToolTip(0, "Specify smoothing factor `a` directly.")
        self.ewm_alpha_spinbox = OptionalDoubleSpinBox(0.1, step=0.1, comparator=lambda val: 0 < val <= 1)
        self.ewm_alpha_spinbox.spinbox.setToolTip("0<a≤1")
        self.setItemWidget(ewm_alpha_item, 1, self.ewm_alpha_spinbox)
        
        # Adjust item for the "Exponentially Weighted" section.
        ewm_adjust_item = QTreeWidgetItem(ewm_item, ["Adjust"])
        ewm_adjust_item.setToolTip(0, "True: Calculate using weights\nFalse: Calculate using recursion")
        self.ewm_adjust_checkbox = QCheckBox()
        self.setItemWidget(ewm_adjust_item, 1, self.ewm_adjust_checkbox)
        
        # ------------ Adaptive Average ------------
        aa_item = QTreeWidgetItem(self, ["Adaptive Average"])
        aa_item.setFirstColumnSpanned(True)
        
        # Enable item for the "Adaptive Average" section.
        adaptive_enable_item = QTreeWidgetItem(aa_item, ["Enable"])
        self.aa_checkbox = QCheckBox()
        self.setItemWidget(adaptive_enable_item, 1, self.aa_checkbox)
        
        # Phase Threshold item for the "Adaptive Average" section.
        adaptive_threshold_item = QTreeWidgetItem(aa_item, ["Phase Threshold"])
        self.aa_threshold_spinbox = QDoubleSpinBox()
        self.aa_threshold_spinbox.setValue(0.5)
        self.aa_threshold_spinbox.setSingleStep(0.25)
        self.aa_threshold_spinbox.setToolTip("The phase change threshold to disable averaging.")
        self.setItemWidget(adaptive_threshold_item, 1, self.aa_threshold_spinbox)
        
         # Number of Points (for calculating average) item for the "Adaptive Average" section.
        adaptive_threshold_item = QTreeWidgetItem(aa_item, ["Number of Points"])
        self.aa_pnts_spinbox = QSpinBox()
        self.aa_pnts_spinbox.setAlignment(SPINBOX_ALIGNMENT)
        self.aa_pnts_spinbox.setMinimum(1)
        self.aa_pnts_spinbox.setValue(8)
        self.aa_pnts_spinbox.setToolTip("Number of points to consider in calculations.")
        self.setItemWidget(adaptive_threshold_item, 1, self.aa_pnts_spinbox)
        
        # Connect signals to disable radio buttons in EWM section when a radio button is clicked.
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
        """
        Get the the user-selected parameters as a dictionary.

        Returns:
            dict: A dictionary of keyword arguments for original, rolling window, ewm, and adaptive average.
        """
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
        """
        Update the tree widget with specified parameters.

        Args:
            kwargs (dict): A dictionary containing parameters to update the tree widget.
        """
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
    """
    This class represents a QWidget containing a radio button and a double spin box.

    Attributes:
        prev_value (float): The previous value of the spin box.
        comparator (function): A function to validate the spin box value.
        ERROR (float): A small value for error tolerance in value comparisons.

        radiobutton (QRadioButton): The radio button to enable or disable the spin box.
        spinbox (QDoubleSpinBox): The double spin box for numerical input.

    Signals:
        disableOtherRadioButtons (pyqtSignal): Signal emitted to disable other radio buttons.

    Methods:
        onValueChanged: Slot method to handle value changes in the spin box.
        value: Get the current value of the spin box.
        setValue: Set the value of the spin box.
        setEnabled: Enable or disable the spin box and radio button.
        isEnabled: Check if the spin box is enabled.

    """
    disableOtherRadioButtons = pyqtSignal()
    
    def __init__(self, initial_value: float, step: float = 0.25, comparator=lambda value: 0 <= value <= float("Inf")):
        """
        Initializes a new OptionalDoubleSpinBox instance.

        Args:
            initial_value (float): The initial value for the spin box.
            step (float): The step value for the spin box.
            comparator (function): A function to validate the spin box value.

        Raises:
            ValueError: If the initial value is not within bounds.
        """
        super().__init__()
        
        # Validate initial value
        if not comparator(initial_value):
            raise ValueError(f"Initial value must be within bounds.")
        
        # Initialize instance variables
        self.prev_value = initial_value
        self.comparator = comparator
        self.ERROR = 1e-5
        
        # Set up radio button
        self.radiobutton = QRadioButton()
        self.radiobutton.clicked.connect(lambda: self.setEnabled(True))
        self.radiobutton.clicked.connect(lambda: self.disableOtherRadioButtons.emit())
        self.radiobutton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Set up double spin box
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setAlignment(SPINBOX_ALIGNMENT)
        self.spinbox.setValue(initial_value)
        self.spinbox.setSingleStep(step)
        self.spinbox.valueChanged.connect(self.onValueChanged)
        
        # Set up layout
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.radiobutton)
        layout.addWidget(self.spinbox)
        self.setLayout(layout)
        
    
    def onValueChanged(self, value: float) -> None:
        """
        Slot method to handle value changes in the spin box.

        Args:
            value (float): The new value of the spin box.
        """
        self.spinbox.blockSignals(True)
        if not self.comparator(value - self.ERROR) or not self.comparator(value + self.ERROR):
            self.spinbox.setValue(self.prev_value)
        self.spinbox.blockSignals(False)
        
        self.prev_value = self.spinbox.value()
        
    def value(self):
        """
        Get the current value of the spin box.

        Returns:
            float: The current value of the spin box, or None if disabled.
        """
        return self.spinbox.value() if self.isEnabled() else None
    
    def setValue(self, value):
        """
        Set the value of the spin box.

        Args:
            value: The value to set. If float, the spin box is enabled with the given value.
                   If None, the spin box is disabled.
        """
        if isinstance(value, float):
            self.setEnabled(True)
            self.spinbox.setValue(value)
        elif value is None:
            self.setEnabled(False)
            
    def setEnabled(self, b: bool):
        """
        Enable or disable the spin box and radio button.

        Args:
            b (bool): True to enable, False to disable.
        """
        self.radiobutton.setChecked(b)
        self.spinbox.setEnabled(b)
        
    def isEnabled(self) -> bool:
        """
        Check if the spin box is enabled.

        Returns:
            bool: True if the spin box is enabled, False otherwise.
        """
        return self.radiobutton.isChecked()

class PaletteButton(QPushButton):
    """
    This class represents a QPushButton that allows selecting a color using QColorDialog.

    Methods:
        setColor: Set the color of the button.
        _showColorDialog: Show the QColorDialog when the button is pressed.
    """
    def __init__(self):
        """
        Initializes a new PaletteButton instance.
        """
        super().__init__()
        self.setColor("")
        self.pressed.connect(self._showColorDialog)
        
    def setColor(self, color: str):
        """
        Set the color of the button.

        Args:
            color (str): The color in hex-code format.
        """
        self.color = color
        self.setStyleSheet(f"background-color: {color};")  # hex-code
        
    def _showColorDialog(self):
        """
        Show the QColorDialog and set the color if valid.
        """
        color = QColorDialog.getColor(QColor(self.color))

        if color.isValid():
            self.setColor(color.name())