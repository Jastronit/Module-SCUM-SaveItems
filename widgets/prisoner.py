from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QLabel, QHBoxLayout, QApplication
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap, QPalette
import os

# ////---- Jednoduchá detekcia dark mode ----////
# Táto funkcia by mala fungovať na všetkých platformách
def is_dark_mode():
    palette = QApplication.instance().palette()
    window_color = palette.color(QPalette.Window)
    # jednoduchá heuristika: ak je pozadie tmavé, berieme to ako dark mode
    return window_color.lightness() < 128

# ////---- Vytvorenie widgetu konzoly ----////
def create_widget(BaseClass, module_name):
    class PrisonerWidget(BaseClass):
        def __init__(self):
            super().__init__(module_name)

            # layout
            layout = QVBoxLayout(self)
            self.setLayout(layout)

            self.setMinimumSize(333, 100)
            self.setMaximumSize(4000, 150)

            # banner
            if is_dark_mode():
                banner_path = os.path.join(os.path.dirname(__file__), "../assets/banners/SINGLEPLAYER.png")
            else:
                banner_path = os.path.join(os.path.dirname(__file__), "../assets/banners/SINGLEPLAYER_DARK.png")
            if os.path.exists(banner_path):
                self.banner = QLabel()
                pixmap = QPixmap(banner_path)
                self.banner.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                # zväčšenie / prispôsobenie na šírku widgetu
                self.banner.setPixmap(pixmap.scaledToHeight(32, Qt.SmoothTransformation))
                self.banner.setAlignment(Qt.AlignCenter)
                layout.addWidget(self.banner)

            # PRISONER
            prisoner_layout = QHBoxLayout()
            prisoner_banner = QLabel()
            if is_dark_mode():
                prisoner_banner.setPixmap(QPixmap(os.path.join(os.path.dirname(__file__), "../assets/banners/PRISONER.png")).scaledToHeight(24, Qt.SmoothTransformation))
            else:
                prisoner_banner.setPixmap(QPixmap(os.path.join(os.path.dirname(__file__), "../assets/banners/PRISONER_DARK.png")).scaledToHeight(24, Qt.SmoothTransformation))
            prisoner_layout.addWidget(prisoner_banner)

            self.prisoner_value = QLabel("N/A")
            self.prisoner_value.setStyleSheet("font-size: 16px; font-weight: bolt; color: #ff8000;")
            self.prisoner_value.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            prisoner_layout.addWidget(self.prisoner_value)

            layout.addLayout(prisoner_layout)

            # SAVE ZONES
            zones_layout = QHBoxLayout()
            zones_banner = QLabel()
            if is_dark_mode():
                zones_banner.setPixmap(QPixmap(os.path.join(os.path.dirname(__file__), "../assets/banners/SAVEZONES.png")).scaledToHeight(24, Qt.SmoothTransformation))
            else:
                zones_banner.setPixmap(QPixmap(os.path.join(os.path.dirname(__file__), "../assets/banners/SAVEZONES_DARK.png")).scaledToHeight(24, Qt.SmoothTransformation))
            zones_layout.addWidget(zones_banner)

            self.zones_value = QLabel("0")
            self.zones_value.setStyleSheet("font-size: 16px; font-weight: bolt; color: #ff8000;")
            self.zones_value.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            zones_layout.addWidget(self.zones_value)

            layout.addLayout(zones_layout)

            # test counter
            self.counter = 0

            # timer na pravidelný update
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_widget)
            self.timer.start(1000)  # každú sekundu

        def update_widget(self):
            # Len refreshuje hodnoty z data.ini
            self.counter += 1

            data_file = self.get_data_path("data.ini")

            prisoner_name = "N/A"
            all_zones_count = "0"

            # načítanie data.ini
            if os.path.exists(data_file):
                import configparser
                config = configparser.ConfigParser()
                config.read(data_file)

                if "prisoner" in config and "name" in config["prisoner"]:
                    prisoner_name = config["prisoner"]["name"]
                if "all_zones" in config and "count" in config["all_zones"]:
                    all_zones_count = config["all_zones"]["count"]

            # ⚡️ tu nastavíš labely aby sa UI obnovilo
            self.prisoner_value.setText(prisoner_name)
            self.zones_value.setText(all_zones_count)

        def close_widget(self):
            # zastavenie timeru
            self.timer.stop()

    return PrisonerWidget()

# ////---- Predvolená pozícia dock widgetu ----////
def get_widget_dock_position():
    return Qt.LeftDockWidgetArea, 0 # oblasť, poradie