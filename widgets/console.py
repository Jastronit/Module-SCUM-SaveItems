from PySide6.QtWidgets import QTextEdit, QVBoxLayout
from PySide6.QtCore import QTimer, Qt
import os

# ////---- Vytvorenie widgetu konzoly ----////
def create_widget(BaseClass, module_name):
    class ConsoleWidget(BaseClass):
        def __init__(self):
            super().__init__(module_name)

            # layout
            layout = QVBoxLayout(self)
            self.setLayout(layout)

            # konzola
            self.text = QTextEdit()
            self.text.setReadOnly(True)
            layout.addWidget(self.text)

            # test counter
            self.counter = 0

            # timer na pravidelný update
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_widget)
            self.timer.start(1000)  # každú sekundu

        def update_widget(self):
            """Len refreshuje hodnoty z data.ini + log.txt"""
            self.counter += 1

            data_file = self.get_data_path("data.ini")
            log_file = self.get_data_path("log.txt")

            prisoner_name = "N/A"
            all_zones_count = "0"
            log_lines = []

            # načítanie data.ini
            if os.path.exists(data_file):
                import configparser
                config = configparser.ConfigParser()
                config.read(data_file)

                if "prisoner" in config and "name" in config["prisoner"]:
                    prisoner_name = config["prisoner"]["name"]
                if "all_zones" in config and "count" in config["all_zones"]:
                    all_zones_count = config["all_zones"]["count"]

            # načítanie log.txt
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    log_lines = f.readlines()[-64:]  # posledných 64 riadkov

            # vyčistenie a vypísanie do konzoly
            self.text.clear()
            self.text.append(f"[{self.counter}] Prisoner name: {prisoner_name}")
            self.text.append(f"[{self.counter}] All zones count: {all_zones_count}")
            self.text.append("\n--- Log ---")
            for line in log_lines:
                self.text.append(line.strip())

        def close_widget(self):
            # zastavenie timeru a vyčistenie textu
            self.timer.stop()
            self.text.clear()

    return ConsoleWidget()

# ////---- Predvolená pozícia dock widgetu ----////
def get_widget_dock_position():
    return Qt.LeftDockWidgetArea