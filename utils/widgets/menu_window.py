from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget, QCheckBox, QLineEdit, QScrollArea, QSizePolicy
from PyQt6.QtCore import Qt
from utils.communicator import Communicator
from utils.widgets.saved_location import SavedLocation
from utils.widgets.button import Button
import requests
import json


location_finder_url = "https://ipinfo.io/json"


class MenuWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.gmt_communicator = Communicator()
        self.loc_communicator = Communicator()
        self.user_gmt_communicator = Communicator()
        self.gmt_changed_signal = self.gmt_communicator.signal
        self.location_changed_signal = self.loc_communicator.signal
        self.user_gmt_signal = self.user_gmt_communicator.signal
        self.parent = parent
        self.location_widgets = list()
        self.log = open("./local/data/log.txt", "w")
        self.init_UI()

    def init_UI(self):
        self.setStyleSheet("background-color: #FFFFFF; color: #000000;")
        self.main_stack = QStackedWidget(self)

        self.main_lyt = self.main_ui()
        self.sett_lyt = self.setting_ui()

        self.main_stack.addWidget(self.main_lyt)
        self.main_stack.addWidget(self.sett_lyt)

        central_layout = QVBoxLayout()
        central_layout.addWidget(self.main_stack)
        self.setLayout(central_layout)

    def change_gmt(self, gmt):
        self.gmt_changed_signal.emit(int(gmt))

    def get_current_locationf(self):
        global location_finder_url
        lat, lon = 0, 0
        try:
            response = requests.get(location_finder_url)

            if response.status_code == 200:
                location_info = response.json()
                city, country, lat, lon = location_info["city"], location_info["country"], * \
                    location_info["loc"].split(',')
                self.log.write("Location Information:\n")
                self.log.write(f"{city}, {country}, {lat}, {lon}\n")
            else:
                self.log.write(
                    f"Error: Unable to fetch location information (Status code: {response.status_code})\n")
        except Exception as e:
            self.log.write(f"An error occurred: {e}\n")

        self.location_changed_signal.emit([city, country, lat, lon])

    def setting_ui(self):
        self.settings = QWidget()
        self.settings_layout = QVBoxLayout()

        self.exit_button = Button("Выйти в меню", self)
        self.exit_button.clicked.connect(self.show_main)
        self.settings_layout.addWidget(self.exit_button)

        self.set_l1 = QHBoxLayout()
        self.set_l2 = QHBoxLayout()
        with open("./local/data/user_app_configuration.json", "r") as f:
            file_ = json.load(f)
        self.custom_loc_cb = QCheckBox()
        if file_["custom_location_on_start"] == "True":
            self.custom_loc_cb.setChecked(True)

        try:
            open("./local/data/locations.txt", "r").read().splitlines()[0]
        except:
            self.custom_loc_cb.setEnabled(False)

        self.custom_loc_label = QLabel(
            "Использовать последнюю сохраненную локацию при старте")
        self.custom_loc_label.setWordWrap(True)
        self.custom_loc_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.custom_loc_cb.clicked.connect(
            lambda: self.custom_loc_cb_clicked(file_))
        self.set_l1.addWidget(self.custom_loc_cb)
        self.set_l1.addWidget(self.custom_loc_label)

        self.gmt_default_lyt = QVBoxLayout()
        self.cb_layout = QHBoxLayout()
        self.default_gmt_cb = QCheckBox()
        self.gmt_input_sett = QLineEdit()
        self.gmt_input_sett.setText(str(file_["gmt"]))
        self.gmt_input_sett.textChanged.connect(
            lambda: self.gmt_input_update_setting(file_)
        )
        self.mini_error_label = QLabel()
        self.mini_error_label.setWordWrap(True)
        self.mini_error_label.setStyleSheet(
            "color: red; font-weight: 200;"
        )
        if file_["default_gmt_is_user_gmt"] == "True":
            self.default_gmt_cb.setChecked(True)
            self.gmt_input_sett.setEnabled(True)
        else:
            self.gmt_input_sett.setEnabled(False)
        self.default_gmt_label = QLabel(
            "Использовать пользовательское смещение GMT")
        self.default_gmt_label.setWordWrap(True)
        self.default_gmt_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.default_gmt_cb.clicked.connect(
            lambda: self.default_gmt_cb_clicked(file_))

        self.cb_layout.addWidget(self.default_gmt_cb)
        self.cb_layout.addWidget(self.default_gmt_label)
        self.gmt_default_lyt.addLayout(self.cb_layout)
        self.gmt_default_lyt.addWidget(self.gmt_input_sett)
        self.gmt_default_lyt.addWidget(self.mini_error_label)
        self.set_l2.addLayout(self.gmt_default_lyt)

        self.settings_layout.addLayout(self.set_l1)
        self.settings_layout.addLayout(self.set_l2)

        self.settings.setLayout(self.settings_layout)

        return self.settings

    def main_ui(self):
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(
            QLabel("Menu"), alignment=Qt.AlignmentFlag.AlignHCenter)

        self.gmt_input_layout = QHBoxLayout()
        self.gmt_input_field = QLineEdit()
        self.gmt_input_field.setPlaceholderText("Смещение GMT")
        self.gmt_input_field.textChanged.connect(
            lambda: self.gmt_menu_update()
        )
        self.gmt_input_layout.addWidget(self.gmt_input_field)
        self.gmt_input_button = Button("Подтвердить", self)
        self.gmt_input_button.change_state(False)
        self.gmt_input_button.clicked.connect(
            lambda: self.change_gmt(self.gmt_input_field.text()))
        self.gmt_input_layout.addWidget(self.gmt_input_button)
        self.user_gmt_button = Button("Сбросить", self)
        self.user_gmt_button.clicked.connect(
            lambda: self.user_gmt_signal.emit(1))
        self.gmt_input_layout.addWidget(self.user_gmt_button)
        self.main_layout.addLayout(self.gmt_input_layout)

        self.use_current_location = Button(
            "Использовать\nтекущее\nместоположение", self)
        self.use_current_location.clicked.connect(
            lambda: self.get_current_locationf()
        )
        self.main_layout.addWidget(self.use_current_location)

        self.locations_scroll = QScrollArea()
        self.loc_widget = QWidget()
        self.loc_widget_layout = QVBoxLayout()

        self.settings_button = Button("Настройки", self)
        self.settings_button.clicked.connect(
            lambda: self.show_settings()
        )
        self.main_layout.addWidget(self.settings_button)

        for location in self.parent.locations:
            widget = SavedLocation(location)
            widget.delete_signal.connect(
                lambda _, w=widget: self.parent.change_saved_state_signal.emit(
                    w.location_label.text())
            )
            widget.use_signal.connect(
                lambda _, w=widget: self.parent.use_loc_signal.emit(
                    w.location_label.text().split(", "))
            )
            self.location_widgets.append(widget)
            self.loc_widget_layout.addWidget(widget)

        self.loc_widget.setLayout(self.loc_widget_layout)
        self.locations_scroll.setWidget(self.loc_widget)
        self.main_layout.addWidget(self.locations_scroll)

        self.main_widget.setLayout(self.main_layout)
        return self.main_widget

    def show_main(self):
        self.main_stack.setCurrentIndex(0)

    def show_settings(self):
        self.main_stack.setCurrentIndex(1)

    def custom_loc_cb_clicked(self, file_):
        if self.custom_loc_cb.isChecked():
            file_["custom_location_on_start"] = "True"
        else:
            file_["custom_location_on_start"] = "False"
        self.file_dump(file_)

    def default_gmt_cb_clicked(self, file_):
        if self.default_gmt_cb.isChecked():
            file_["default_gmt_is_user_gmt"] = "True"
            self.gmt_input_sett.setEnabled(True)
            self.gmt_input_sett.setPlaceholderText("Смещение GMT")
        else:
            file_["default_gmt_is_user_gmt"] = "False"
            self.gmt_input_sett.setEnabled(False)
            self.gmt_input_sett.setPlaceholderText("")
        self.file_dump(file_)

    def file_dump(self, file_):
        with open("./local/data/user_app_configuration.json", "w") as f:
            json.dump(file_, f, indent=4)

    def gmt_input_update_setting(self, file_):
        gmt_offset = self.gmt_input_sett.text()
        try:
            gmt_offset = int(gmt_offset)
        except ValueError:
            self.mini_error_label.setText(
                "В поле 'Смещение GMT' можно ввести только целое число"
            )
        else:
            self.mini_error_label.clear()
            file_["gmt"] = str(gmt_offset)
        self.file_dump(file_)

    def gmt_menu_update(self):
        gmt = self.gmt_input_field.text()
        try:
            int(gmt)
            if not gmt:
                raise ValueError
        except ValueError:
            self.gmt_input_button.change_state(False)
        else:
            self.gmt_input_button.change_state(True)
