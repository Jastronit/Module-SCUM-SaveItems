from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QLabel, QApplication
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
    class ConsoleWidget(BaseClass):
        def __init__(self):
            super().__init__(module_name)

            # layout
            layout = QVBoxLayout(self)
            self.setLayout(layout)

            self.setMinimumSize(100, 50)

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
            log_file = self.get_data_path("log.txt")

            log_lines = []

            # načítanie log.txt
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    log_lines = f.readlines()[-64:]  # posledných 64 riadkov

            # vyčistenie a vypísanie do konzoly
            self.text.clear()
            for line in log_lines:
                self.text.append(line.strip())

        def close_widget(self):
            # zastavenie timeru a vyčistenie textu
            self.timer.stop()
            self.text.clear()

    return ConsoleWidget()

# ////---- Predvolená pozícia dock widgetu ----////
def get_widget_dock_position():
    return Qt.LeftDockWidgetArea, 1  # oblasť, poradie
