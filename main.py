import sys
from PyQt6.QtWidgets import QMainWindow, QGraphicsScene, QListWidget, QWidget, QVBoxLayout, QScrollArea, QApplication, QMessageBox
from PyQt6 import uic
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSlot
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from utils.communicator import Communicator
from utils.apis.fetch_weather import process_change
from utils.error_data import *
from utils.widgets.error_window import ErrorWindow
from utils.apis.fetch_location import search_location
from utils.widgets.menu_window import MenuWidget
from utils.widgets.saved_location import SavedLocation
from utils.widgets.button import Button
import datetime as dt
import json
import codecs
from screeninfo import get_monitors


lat, lon = 0, 0
gmt_offset = 0


class WeatherApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.log = codecs.open("./local/data/log.txt", "w", "utf-8")

        self.get_new_loc = True

        self.signals = Communicator()
        self.change_saved_state_communicator = Communicator()
        self.change_saved_state_signal = self.change_saved_state_communicator.signal

        self.completer_wait = QTimer(self)
        self.completer_wait.setSingleShot(True)
        self.completer_wait.setInterval(500)
        self.completer_wait.timeout.connect(
            lambda: self.search_bar_gateway())

        with codecs.open("./local/data/locations.txt", "r", "utf-8") as f:
            locs = f.read().splitlines()
            try:
                self.last = locs[-1].split(", ")
            except IndexError:
                pass
            self.locations = set(locs)

        self.use_loc_comm = Communicator()
        self.use_loc_signal = self.use_loc_comm.signal

        self.wait = False
        self.temp_search_bar = ''
        uic.loadUi('./source/untitled.ui', self)
        self.now_button.click()
        self.initUI()

    def initUI(self):
        self.setMaximumSize(get_monitors()[0].width, get_monitors()[0].height)

        self.completer_widget = QListWidget(self)
        self.completer_widget.hide()

        self.custom_signal = self.signals.signal

        self.buttons = [self.now_button, self.today_button,
                        self.tmrw_button, self.days3_button, self.days10_button]
        self.buttons[0].clicked.connect(
            lambda: self.custom_signal.emit(self.buttons[0]))
        self.buttons[1].clicked.connect(
            lambda: self.custom_signal.emit(self.buttons[1]))
        self.buttons[2].clicked.connect(
            lambda: self.custom_signal.emit(self.buttons[2]))
        self.buttons[3].clicked.connect(
            lambda: self.custom_signal.emit(self.buttons[3]))
        self.buttons[4].clicked.connect(
            lambda: self.custom_signal.emit(self.buttons[4]))
        self.custom_signal.connect(lambda x: self.change_time_interval(x))

        self.weather_info = [
            self.weather_info1, self.weather_info2,
            self.weather_info3, self.weather_info4,
            self.weather_info5, self.weather_info6,
            self.weather_info7, self.weather_info8,
            self.weather_info9, self.weather_info10
        ]

        self.time_label = [
            self.time_label1, self.time_label2, self.time_label3,
            self.time_label4, self.time_label5, self.time_label6,
            self.time_label7, self.time_label8, self.time_label9,
            self.time_label10
        ]

        self.icons = {
            self.icon1: QGraphicsScene(), self.icon2: QGraphicsScene(),
            self.icon3: QGraphicsScene(), self.icon4: QGraphicsScene(),
            self.icon5: QGraphicsScene(), self.icon6: QGraphicsScene(),
            self.icon7: QGraphicsScene(), self.icon8: QGraphicsScene(),
            self.icon9: QGraphicsScene(), self.icon10: QGraphicsScene()
        }

        self.menu = MenuWidget(self)
        self.menu.hide()
        self.menu.resize(0, self.height())
        self.menu.move(0, 0)
        self.centralwidget.layout().insertWidget(0, self.menu)
        self.menu_button.clicked.connect(lambda: self.menu_state_change())
        self.menu.gmt_changed_signal.connect(lambda x: self.change_gmt(x))
        self.menu.location_changed_signal.connect(
            lambda x: self.change_location(x))
        self.menu.user_gmt_signal.connect(
            lambda: self.change_gmt("placeholder"))

        self.save_button.clicked.connect(
            lambda: self.change_saved_state_signal.emit(self.location.text())
        )
        self.change_saved_state_signal.connect(
            lambda loc: self.save_delete_loc(loc)
        )
        self.use_loc_signal.connect(lambda loc: self.change_location(loc))

        # on start up
        self.config = json.load(
            codecs.open("./local/data/user_app_configuration.json", "r", "utf-8"))

        if self.config["custom_location_on_start"] == "True":
            self.change_location(self.last)
        else:
            self.menu.get_current_locationf()

        if self.config["default_gmt_is_user_gmt"] == "True":
            self.change_gmt(int(self.config["gmt"]))
        self.change_time_interval(Button("Сейчас"))

        if gmt_offset >= 0:
            self.current_time.setText(
                "Сейчас " + (dt.datetime.now() + dt.timedelta(hours=gmt_offset)).strftime("%d.%m.%Y %H:%M"))
        else:
            self.current_time.setText(
                "Сейчас " + (dt.datetime.now() - dt.timedelta(hours=gmt_offset)).strftime("%d.%m.%Y %H:%M"))
        self.temp_search_bar = self.search_bar.text()
        self.search_bar.textChanged.connect(lambda: self.completer_timer())

        self.find_loc_button.clicked.connect(
            lambda: self.get_final_location(
                self.search_bar.text().split(", "))
        )

    @pyqtSlot(object)
    def change_gmt(self, gmt="0"):
        global gmt_offset
        try:
            gmt = int(gmt)

            gmt_offset = gmt
            self.log.write("GMT offset set to " + str(gmt_offset) + "\n")
            if gmt_offset >= 0:
                self.current_time.setText(
                    "Сейчас " +
                    (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=gmt_offset)
                     ).strftime("%d.%m.%Y %H:%M")
                )
            else:
                self.current_time.setText(
                    "Сейчас " +
                    (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=gmt_offset)
                     ).strftime("%d.%m.%Y %H:%M")
                )
        except ValueError:
            gmt_offset = self.get_gmt_offset()
            self.current_time.setText(
                "Сейчас " + dt.datetime.now().strftime("%d.%m.%Y %H:%M")
            )
            if gmt_offset >= 0:
                self.log.write(
                    f"UTC offset is set to user(+{gmt_offset}) hours.\n")
            else:
                self.log.write(
                    f"UTC offset is set to user(-{gmt_offset}) hours.\n")
        self.time_label_update()

    @pyqtSlot(object)
    def change_location(self, loc):
        global lat, lon
        self.log.write(f"Location changed to: {loc}\n")
        lat, lon = loc[-2::]
        arg = ", ".join(loc)

        if arg in self.locations:
            self.save_button.setText("Удалить")
        else:
            self.save_button.setText("Сохранить")
        self.set_location_text(arg)

    def get_gmt_offset(self):
        utc_now = dt.datetime.now(dt.timezone.utc)

        local_time = utc_now.astimezone()

        utc_offset = local_time.utcoffset()

        if utc_offset is not None:
            utc_offset = utc_offset.total_seconds() // 3600
            return int(utc_offset)
        else:
            self.log.write("UTC offset is not available.\n")
            return 0

    def search_bar_gateway(self):
        if self.get_new_loc:
            self.get_location_completer(self.search_bar.text().split(", "))
        else:
            self.get_new_loc = True

    def time_label_update(self):
        global gmt_offset
        if len(self.time_labelH.text().split("(")) == 2:
            parts = self.time_labelH.text().split("(")
            if gmt_offset > 0:
                parts[1] = f"(GMT+{gmt_offset})^^^"
            elif gmt_offset < 0:
                parts[1] = f"(GMT{gmt_offset})^^^"
            else:
                parts[1] = "(GMT)^^^"
            time_new = parts[0] + parts[1]
            self.time_labelH.setText(time_new)

    def change_time_interval(self, button):
        global lat, lon, gmt_offset

        for i in self.buttons:
            i.setStyleSheet("background-color: #ffffff;")
        button.setStyleSheet("background-color: #8bfca5;")
        return_data = ''
        try:
            return_data = process_change(button.text(), lat, lon)
        except WeatherDataError as err:
            self.show_error(err)
            self.log.write(str(err) + "\n")
        except Exception as err:
            self.show_error("Unexpected error: " + str(err))
            self.log.write("Got unexpected error: " + str(err) + "\n")
        else:
            self.log.write("Weather data received\n")
            self.my_gmt = self.get_gmt_offset()
            tmp_type = False
            for i in range(10):
                time = list(return_data[0].keys())[i]
                self.weather_info[i].setText(return_data[0][time])

                if button.text() == "Сейчас" or button.text() == "Сегодня" or button.text() == "Завтра":
                    self.time_label[i].setText(
                        str(time % 24) + ":00" + "\n" + str((time - self.my_gmt + gmt_offset) % 24) + ":00\n")
                    tmp_type = 1
                elif button.text() == "3 дня":
                    self.time_label[i].setText(
                        (dt.datetime.now() + dt.timedelta(days=(time-24)//24)).strftime("%d.%m") + '\n' + str(time % 24 + gmt_offset) + ":00" + "\n" + str((time + gmt_offset) % 24) + ":00\n")
                    tmp_type = 2
                else:
                    self.time_label[i].setText(
                        (dt.datetime.now() + dt.timedelta(days=i)).strftime("%d.%m"))
                    tmp_type = 3

            match tmp_type:
                case 1:
                    self.time_labelH.setText(
                        "Системное время\nПользоват. время\n(GMT)^^^"
                    )
                    self.time_label_update()
                case 2:
                    self.time_labelH.setText(
                        "Дата\nСистемное время\nПользоват. время\n(GMT)^^^"
                    )
                    self.time_label_update()
                case 3:
                    self.time_labelH.setText(
                        "Дата"
                    )

            if button.text() == "Сейчас":
                self.time_label[2].setText("Сейчас")
                self.time_label[2].setStyleSheet("background-color: #8bfca5;")
            elif self.time_label[2].text() != "Сейчас":
                self.time_label[2].setStyleSheet("background-color: #ffffff;")
            self.draw_icons(return_data[1])

    def draw_icons(self, data):
        for i in range(len(data)):
            self.icons[list(self.icons.keys())[i]].clear()
            self.svg_item = QGraphicsSvgItem(data[i])
            self.icons[list(self.icons.keys())[i]].addItem(self.svg_item)

            list(self.icons.keys())[i].setScene(
                self.icons[list(self.icons.keys())[i]])

    def show_error(self, err):
        error_window = ErrorWindow(err)

    def completer_timer(self):
        try:
            self.completer_widget.hide()
        except:
            pass

        if self.temp_search_bar != self.search_bar.text():
            self.completer_wait.stop()
            self.completer_wait.start()

    def get_location_completer(self, loc):
        self.setCursor(QCursor(Qt.CursorShape.WaitCursor))
        self.completer_widget.clear()
        loc_data = list()

        try:
            loc_data = search_location(loc[0])
        except LocationDataError as err:
            self.show_error(str(err))
        except Exception as err:
            self.show_error("Unexpected error: " + str(err))
            self.log.write("Got unexpected error: " + str(err) + "\n")
        else:
            self.log.write("Location request successful\n")

        place_names = list()
        if loc_data:
            sbar = self.search_bar.text().split(', ')
            sbar = [param.strip() for param in sbar if param.strip()]
            self.log.write("Location data received\nLocation data:\n")
            for location in loc_data:
                city = location["name"]
                country = location["parentRegions"][-2]["name"] if len(
                    location["parentRegions"]) > 1 else ""
                latitude = str(location["latitude"])
                longitude = str(location["longitude"])
                self.log.write(f"{city}, {country}, {latitude} {longitude}\n")

                fields = [city, country, latitude, longitude]
                matched = True

                for i in range(len(sbar)):
                    if sbar[i].lower() not in fields[i].lower():
                        self.log.write(
                            f"Not matched {sbar[i]}   and   {fields}")
                        matched = False
                        break

                if matched:
                    place_names.append(
                        ", ".join([city, country, latitude, longitude]))

        if not place_names:
            place_names.append("Ничего не найдено")

        self.completer_widget.addItems(place_names)
        self.completer_widget.move(
            QPoint(self.search_bar.x() + 9, self.search_bar.y() + 29))
        self.completer_widget.resize(self.search_bar.width(), 100)
        self.completer_widget.show()
        self.completer_wait.stop()

        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        self.completer_widget.currentItemChanged.connect(
            lambda: self.completer_item_selected())

    def completer_item_selected(self):
        if self.completer_widget.currentItem():
            self.get_new_loc = False
            self.search_bar.setText(self.completer_widget.currentItem().text())

        self.completer_widget.hide()

    def get_final_location(self, loc):
        global lat, lon
        loc_data = list()
        sbar = list()
        try:
            loc_data = search_location(loc[0])
            sbar = self.search_bar.text().split(', ')
        except LocationDataError as err:
            self.show_error(str(err))
        else:
            self.log.write("Location request successful\n")

        if len(loc) > 4:
            self.show_error("Invalid location input")
            return

        loc = [item for item in loc if item]
        sbar = [item for item in sbar if item]

        matched_location = None
        matched = True
        for location in loc_data:
            city = location["name"]
            country = location["parentRegions"][-2]["name"] if len(
                location["parentRegions"]) > 1 else ""
            latitude = str(location["latitude"])
            longitude = str(location["longitude"])

            fields = [city, country, latitude, longitude]

            for i in range(len(sbar)):
                if sbar[i].lower() not in fields[i].lower():
                    self.log.write(f"Not matched {sbar[i]}   and   {fields}")
                    matched = False
                    break

            if matched:
                matched_location = location
                break

        if matched_location:
            lat, lon = str(matched_location["latitude"]), str(
                matched_location["longitude"])
            self.completer_widget.hide()
            self.search_bar.setText('')
            self.set_location_text(
                ", ".join([matched_location["name"], matched_location["parentRegions"][-2]["name"], lat, lon]))
            if ", ".join([matched_location["name"], matched_location["parentRegions"][-2]["name"], lat, lon]) in self.locations:
                self.save_button.setText("Удалить")
            else:
                self.save_button.setText("Сохранить")
        else:
            self.show_error("Локация не найдена")

    def set_location_text(self, text):
        self.location.setText(text)
        self.change_time_interval(Button("Сейчас"))

    def menu_state_change(self):
        if self.menu.isVisible():
            self.menu.hide()
            self.log.write("MenuWidget hidden\n")
        else:
            self.menu.show()
            self.log.write("MenuWidget shown\n")

        self.completer_widget.move(
            QPoint(self.search_bar.x(), self.search_bar.y() + 20))
        self.completer_widget.resize(self.search_bar.width(), 100)

    def save_delete_loc(self, location):
        if location in self.locations:
            self.locations.remove(location)
        else:
            self.locations.add(location)

        if self.location.text() in self.locations:
            self.save_button.setText("Удалить")
        else:
            self.save_button.setText("Сохранить")

        if len(self.locations):
            self.menu.custom_loc_cb.setEnabled(True)

        # save the locations in the file
        with codecs.open("./local/data/locations.txt", "w", "utf-8") as f:
            f.write("\n".join(self.locations))

        self.update_loc_scroll_area()

    def update_loc_scroll_area(self):
        self.menu.main_layout.removeWidget(self.menu.locations_scroll)
        self.menu.locations_scroll = QScrollArea()
        self.menu.loc_widget = QWidget()
        self.menu.loc_widget_layout = QVBoxLayout()
        for loc in self.locations:
            widget = SavedLocation(loc)
            widget.delete_signal.connect(
                lambda _, w=widget: self.change_saved_state_signal.emit(
                    w.location_label.text())
            )
            widget.use_signal.connect(
                lambda _, w=widget: self.use_loc_signal.emit(
                    w.location_label.text().split(", "))
            )
            self.menu.location_widgets.append(widget)
            self.menu.loc_widget_layout.addWidget(widget)
        self.menu.loc_widget.setLayout(self.menu.loc_widget_layout)
        self.menu.locations_scroll.setWidget(self.menu.loc_widget)
        self.menu.main_layout.addWidget(self.menu.locations_scroll)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Выход',
                                     "Вы уверены, что хотите выйти?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.log.close()
            event.accept()
        else:
            event.ignore()

    def resizeEvent(self, event):
        if self.menu.isVisible():
            self.completer_widget.move(
                QPoint(self.menu.x() + self.search_bar.x(), self.search_bar.y() + 29))
        else:
            self.completer_widget.move(
                QPoint(self.search_bar.x() + 9, self.search_bar.y() + 29))
        self.completer_widget.resize(self.search_bar.width(), 100)
        super().resizeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    weather_app = WeatherApp()
    weather_app.show()
    sys.exit(app.exec())
