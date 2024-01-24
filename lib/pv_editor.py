from PyQt6.QtWidgets import QGroupBox, QPushButton, QVBoxLayout, QTableWidget, QHeaderView, QMenu
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

from lib.pv_item import PVItem

# Constants for the PV Editor
GROUPBOX_TEXT = "PV Editor"
ADD_BUTTON_TEXT = "+"
ADD_BUTTON_ALIGNMENT = Qt.AlignmentFlag.AlignRight
ADD_BUTTON_SIZE = (50, 25)  # (width, height)
TABLE_GRID_ENABLED = False
TABLE_HEADER_VISIBLE = (False, False)  # (horizontal, vertical)
TABLE_HORIZONTAL_HEADER_RESIZE_MODE = QHeaderView.ResizeMode.Stretch
TABLE_SELECTION_BEHAVIOR = QTableWidget.SelectionBehavior.SelectRows
TABLE_SELECTION_MODE = QTableWidget.SelectionMode.SingleSelection
TABLE_ROW_HEIGHT = 50
DEFAULT_ITEM_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", 
                       "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]

RW_NAME = lambda name: name + " Rolling-Window"
EWM_NAME = lambda name: name + " Exponentially Weighted"
AA_NAME = lambda name: name + " Adaptive Average"


class PVEditor(QGroupBox):
    """
    Custom PV Editor widget for managing PV items.

    Attributes:
        main_window: Reference to the main window.

    Methods:
        __init__: Initializes the PVEditor with necessary components.
        __iter__: Iterates over PV items in the editor.
        reset: Clears all items from the editor.
        _showTableContextMenu: Shows the context menu when right-clicking on a table row.
        addItem: Adds a new PV item to the editor.
        _onItemParamsUpdated: Handles updates to PV item parameters.
    """
    updated = pyqtSignal()
    
    def __init__(self, main_window):
        """
        Initializes a new PVEditor instance.

        Args:
            main_window: Reference to the main window.
        """
        super().__init__(GROUPBOX_TEXT)
        
        self.main_window = main_window
        
        # Add button for adding new PV items
        self.add_button = QPushButton(ADD_BUTTON_TEXT)
        self.add_button.setFixedSize(ADD_BUTTON_SIZE[0], ADD_BUTTON_SIZE[1])
        self.add_button.pressed.connect(self.addItem)
        
        # Table for displaying PV items
        self.table = QTableWidget(0, 1)
        self.table.setShowGrid(TABLE_GRID_ENABLED)
        self.table.horizontalHeader().setVisible(TABLE_HEADER_VISIBLE[0])
        self.table.horizontalHeader().setSectionResizeMode(TABLE_HORIZONTAL_HEADER_RESIZE_MODE)
        self.table.verticalHeader().setVisible(TABLE_HEADER_VISIBLE[1])
        self.table.setSelectionBehavior(TABLE_SELECTION_BEHAVIOR)
        self.table.setSelectionMode(TABLE_SELECTION_MODE)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._showTableContextMenu)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Set up the layout 
        layout = QVBoxLayout()
        layout.addWidget(self.add_button, alignment=ADD_BUTTON_ALIGNMENT)
        layout.addWidget(self.table)
        self.setLayout(layout)
        
    def __iter__(self):
        """
        Allows iterating over PV items in the editor.
        """
        for row in range(self.table.rowCount()):
            yield self.table.cellWidget(row, 0)
    
    def reset(self):
        """
        Clears all items from the editor.
        """
        self.table.setRowCount(0)
        
    def _showTableContextMenu(self, pos):
        """
        Shows the context menu when right-clicking on a table row.

        Args:
            pos: Position of the right-click.
        """
        def deleteScript():
            self.table.removeRow(self.table.rowAt(pos.y()))
            self.updated.emit()
            
        def clearHistory():
            row = self.table.rowAt(pos.y())
            item = self.table.cellWidget(row, 0)
            item.clearSamples()
            self.updated.emit()
            
        context_menu = QMenu(self.table)
        
        delete_action = QAction("Delete", self.table)
        delete_action.triggered.connect(deleteScript)
        
        clear_action = QAction("Clear History", self.table)
        clear_action.triggered.connect(clearHistory)
        
        context_menu.addAction(delete_action)
        context_menu.addAction(clear_action)
        context_menu.exec(self.table.mapToGlobal(pos))
        
    def addItem(self):
        """
        Adds a new PV item to the editor.

        The method is responsible for creating and adding a new PVItem to the editor's table. It ensures that each PV item
        has a unique color and connects the item's 'paramsChanged' signal to the '_onItemParamsUpdated' slot.

        Returns:
            PVItem: The newly created PV item.
        """
        # List to track unavailable colors
        unavailable_colors = []
        
        # Iterate through existing rows in the table to check colors
        for row in range(self.table.rowCount()):
            item = self.table.cellWidget(row, 0)
            if item:
                color = item.params.get("color", "")
                if color in DEFAULT_ITEM_COLORS:
                    unavailable_colors.append(color)
                    
                    # If all default colors are unavailable, clear the list to start fresh
                    if set(unavailable_colors) == set(DEFAULT_ITEM_COLORS):
                        unavailable_colors.clear()
        
        # Find the first available color from the default set
        for tab_color in DEFAULT_ITEM_COLORS:
            if tab_color not in unavailable_colors:
                color = tab_color
                break
        
        # Create a new PVItem instance
        item = PVItem(self)
        
        # Add a new row to the table and set the cell widget
        new_row = self.table.rowCount()
        self.table.insertRow(new_row)
        self.table.setCellWidget(new_row, 0, item)
        self.table.setRowHeight(new_row, TABLE_ROW_HEIGHT)
        
        # Update the parameters of the new item with the selected color
        item.updateParams({"color": color})
        
        # Connect the 'paramsChanged' signal of the item to the '_onItemParamsUpdated' slot
        item.paramsChanged.connect(self._onItemParamsUpdated)
    
        # Return the newly created PV item
        return item
    
    def _onItemParamsUpdated(self, params):
        """
        Handles updates to PV item parameters.

        Args:
            params: Updated parameters of the PV item.
        """
        kwargs = params.get("kwargs", {})
        og_kwargs = kwargs.get("original", {})
        rw_kwargs = kwargs.get("rolling_window", {})
        ewm_kwargs = kwargs.get("ewm", {})
        aa_kwargs = kwargs.get("adaptive", {})
        
        if self.main_window.canvas.isCurve(params["name"]) and not og_kwargs.get("enabled", False):
            self.main_window.canvas.removeCurve(params["name"])
            
        if self.main_window.canvas.isCurve(RW_NAME(params["name"])) and not rw_kwargs.get("enabled", False):
            self.main_window.canvas.removeCurve(RW_NAME(params["name"]))
            
        if self.main_window.canvas.isCurve(EWM_NAME(params["name"])) and not ewm_kwargs.get("enabled", False):
            self.main_window.canvas.removeCurve(EWM_NAME(params["name"]))
            
        if self.main_window.canvas.isCurve(AA_NAME(params["name"])) and not aa_kwargs.get("enabled", False):
            self.main_window.canvas.removeCurve(AA_NAME(params["name"]))

        self.updated.emit()