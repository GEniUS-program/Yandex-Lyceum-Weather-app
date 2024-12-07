from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from utils.communicator import Communicator


class SavedLocation(QWidget):
    def __init__(self, location, parent=None, flags=Qt.WindowType.WindowStaysOnTopHint) -> None:
        super().__init__(parent, flags)

        self.location = location
        self.delete_communicator = Communicator()
        self.delete_signal = self.delete_communicator.signal
        self.use_communicator = Communicator()
        self.use_signal = self.use_communicator.signal

        self.init_UI()

    def init_UI(self):
        self.widget_layout = QHBoxLayout()

        self.location_label = QLabel(self.location)
        self.widget_layout.addWidget(self.location_label)

        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(
            lambda: self.delete_signal.emit(self.location))
        self.widget_layout.addWidget(self.delete_button)

        self.use_button = QPushButton("Использовать")
        self.use_button.clicked.connect(
            lambda: self.use_signal.emit(self.location))
        self.widget_layout.addWidget(self.use_button)

        self.setLayout(self.widget_layout)
