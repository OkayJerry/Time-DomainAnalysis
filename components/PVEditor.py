from PyQt6.QtWidgets import QWidget, QTableWidget, QHeaderView, QPushButton, QVBoxLayout, QMenu
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

from components.PVItem import PVTableItem

from time import sleep

class PVTable(QTableWidget):
    removedPV = pyqtSignal(str)
    requestProcessRun = pyqtSignal()
    
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
        
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        
    def getNextColor(self) -> str:
        TAB_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
        
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
            
        return color
        
    def addItem(self):
        ROW_HEIGHT = 50
        
        item = PVTableItem()
        item.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.insertRow(self.rowCount())
        self.setCellWidget(self.rowCount() - 1, 0, item)
        self.setRowHeight(self.rowCount() - 1, ROW_HEIGHT)
        
        item.parent().setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        return item
        
    # def keyPressEvent(self, event):
    #     if event.key() == Qt.Key.Key_Backspace:
    #         selected_row = self.currentRow()
    #         self.removeRow(selected_row)
            
    def getItems(self) -> [PVTableItem]:
        return [self.cellWidget(row, 0) for row in range(self.rowCount())]
    
    def reset(self):
        self.setRowCount(0)
        self.addItem()
        
    def loadPVData(self, pv_data: dict):
        for name, values in pv_data.items():
            item = self.addItem()            
            item.loadPVData(name, values)
            
                
    def loadPVParameters(self, params: list):
        for param in params:
            item = self.addItem()
            item.loadPVParameters(param)
            
    def showContextMenu(self, pos):  
        def onDelete():
            row = self.rowAt(pos.y())
            self.cellWidget(row, 0).removal_flag = True
            self.requestProcessRun.emit()

            
        contextMenu = QMenu(self)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(onDelete)
        
        contextMenu.addAction(delete_action)
        contextMenu.exec(self.mapToGlobal(pos))
        
    def removeFlaggedItems(self):
        for row in reversed(range(self.rowCount())):
            item = self.cellWidget(row, 0)
            if item.removal_flag:
                # Required because canvas updates are made from a QThread.
                # It is a hacky solution, but the only one I could figure out
                # without having to redesign a good portion of the software.
                sleep(0.01)  
                
                self.removeRow(row)


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
        
    def reset(self):
        self.table.reset()
        
class TogglePlayButton(QPushButton):
    toggled = pyqtSignal(bool)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.is_playing: bool = False
        
        self.setText("▶")
        self.setFixedSize(25, 25)
        
        self.clicked.connect(self.toggle)
        
    def toggle(self) -> None:
        self.setText("▶" if self.is_playing else "■")
        self.is_playing = not self.is_playing
        self.toggled.emit(self.is_playing)
        
    def reset(self):
        if self.is_playing:
            self.toggle()