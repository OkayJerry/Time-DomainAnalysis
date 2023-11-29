from PyQt6.QtWidgets import QMessageBox

# Global constants for the critical error dialog
TITLE = "Critical Error"
ICON = QMessageBox.Icon.Critical
ERROR_TEXT = "An error occurred..."

class CriticalDialog(QMessageBox):
    """
    Custom critical error dialog for displaying error messages.

    Attributes:
        None

    Methods:
        __init__: Initializes the CriticalDialog with the specified error message and parent widget.
    """
    def __init__(self, error_message: str, parent):
        """
        Initializes a new CriticalDialog instance.

        Args:
            error_message (str): The error message to be displayed.
            parent: The parent widget for the dialog.
        """
        super().__init__(parent)
        
        # Set dialog properties
        self.setWindowTitle(TITLE)
        self.setIcon(ICON)
        self.setText(ERROR_TEXT)
        self.setInformativeText(error_message)