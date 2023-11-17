from PyQt6.QtWidgets import QGroupBox, QPushButton, QVBoxLayout, QTableWidget, QHeaderView, QMenu
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from lib.pv_item import PVItem

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
    def __init__(self, main_window):
        super().__init__(GROUPBOX_TEXT)
        
        self.main_window = main_window
        
        self.add_button = QPushButton(ADD_BUTTON_TEXT)
        self.add_button.setFixedSize(ADD_BUTTON_SIZE[0], ADD_BUTTON_SIZE[1])
        self.add_button.pressed.connect(self.addItem)
        
        self.table = QTableWidget(0, 1)
        self.table.setShowGrid(TABLE_GRID_ENABLED)
        self.table.horizontalHeader().setVisible(TABLE_HEADER_VISIBLE[0])
        self.table.horizontalHeader().setSectionResizeMode(TABLE_HORIZONTAL_HEADER_RESIZE_MODE)
        self.table.verticalHeader().setVisible(TABLE_HEADER_VISIBLE[1])
        self.table.setSelectionBehavior(TABLE_SELECTION_BEHAVIOR)
        self.table.setSelectionMode(TABLE_SELECTION_MODE)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._showTableContextMenu)
                
        layout = QVBoxLayout()
        layout.addWidget(self.add_button, alignment=ADD_BUTTON_ALIGNMENT)
        layout.addWidget(self.table)
        self.setLayout(layout)
        
    def __iter__(self):
        for row in range(self.table.rowCount()):
            yield self.table.cellWidget(row, 0)
    
    def reset(self):
        self.table.setRowCount(0)
        
    def _showTableContextMenu(self, pos):
        context_menu = QMenu(self.table)
        
        delete_action = QAction("Delete", self.table)
        delete_action.triggered.connect(lambda: self.table.removeRow(self.table.rowAt(pos.y())))
        
        context_menu.addAction(delete_action)
        context_menu.exec(self.table.mapToGlobal(pos))
        
    def addItem(self):   
        unavailable_colors = []
        for row in range(self.table.rowCount()):
            item = self.table.cellWidget(row, 0)
            if item:
                color = item.params.get("color", "")
                if color in DEFAULT_ITEM_COLORS:
                    unavailable_colors.append(color)
                    
                    if set(unavailable_colors) == set(DEFAULT_ITEM_COLORS):
                        unavailable_colors.clear()
        
        for tab_color in DEFAULT_ITEM_COLORS:
            if tab_color not in unavailable_colors:
                color = tab_color
                break
            
        item = PVItem(self)
        
        new_row = self.table.rowCount()
        self.table.insertRow(new_row)
        self.table.setCellWidget(new_row, 0, item)
        self.table.setRowHeight(new_row, TABLE_ROW_HEIGHT)
        
        item.updateParams({"color": color})
        
        item.paramsChanged.connect(self._onItemParamsUpdated)
    
        return item
    
    def _onItemParamsUpdated(self, params):
        kwargs = params.get("kwargs", {})
        og_kwargs = kwargs.get("original", {})
        rw_kwargs = kwargs.get("rolling_window", {})
        ewm_kwargs = kwargs.get("ewm", {})
        aa_kwargs = kwargs.get("adaptive", {})
        
        if self.main_window.canvas.isCurve(params["name"]) and not og_kwargs.get("enabled", False):
            self.main_window.canvas.removeCurve(params["name"])
            
        if self.main_window.canvas.isCurve(RW_NAME(params["name"])) and not rw_kwargs.get("enabled", False):
            self.main_window.canvas.removeCurve(params["name"])
            
        if self.main_window.canvas.isCurve(EWM_NAME(params["name"])) and not ewm_kwargs.get("enabled", False):
            self.main_window.canvas.removeCurve(EWM_NAME(params["name"]))
            
        if self.main_window.canvas.isCurve(AA_NAME(params["name"])) and not aa_kwargs.get("enabled", False):
            self.main_window.canvas.removeCurve(AA_NAME(params["name"]))
