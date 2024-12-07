from PyQt6.QtCore import QObject, pyqtSignal


class Communicator(QObject):
    signal = pyqtSignal(object)
