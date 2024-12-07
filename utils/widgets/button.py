from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QCursor, QPixmap
from PyQt6.QtCore import Qt


class Button(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.enabled = True

    def change_state(self, state):
        self.enabled = state
        if self.enabled:
            self.setEnabled(True)
            self.unsetCursor()
        else:
            self.setEnabled(False)

        self.update()

    def enterEvent(self, event):
        if not self.enabled:
            cursor_pixmap = QPixmap(
                "E:\\Yandex Lyceum Weather app\\source\\icons\\forbidden.png")
            cursor_pixmap = cursor_pixmap.scaled(20, 20)
            custom_cursor = QCursor(cursor_pixmap)
            self.parent().setCursor(custom_cursor)
        else:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def leaveEvent(self, event):
        self.parent().unsetCursor()
