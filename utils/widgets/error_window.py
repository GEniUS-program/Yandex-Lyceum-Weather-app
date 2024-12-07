from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel


class ErrorWindow(QWidget):
    def __init__(self, error):
        super().__init__()
        self.setWindowTitle("Ошибка")
        self.setGeometry(100, 100, 300, 150)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(lambda: self.close())

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(QLabel(error))
        self.main_layout.addWidget(self.ok_button)

        self.setLayout(self.main_layout)
        self.show()
