from PyQt6.QtWidgets import QMessageBox

TITLE = "Critical Error"
ICON = QMessageBox.Icon.Critical
ERROR_TEXT = "An error occurred..."

class CriticalDialog(QMessageBox):
    def __init__(self, error_message: str, parent):
        super().__init__(parent)
        
        self.setWindowTitle(TITLE)
        self.setIcon(ICON)
        self.setText(ERROR_TEXT)
        self.setInformativeText(error_message)