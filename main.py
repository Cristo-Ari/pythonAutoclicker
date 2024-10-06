import sys
import time
import threading
import mouse
import ctypes
from pynput import keyboard
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QRadioButton, QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# Константы для использования в низкоуровневых функциях Windows API
VK_CODE = {
    'shift': 0x10,
    'ctrl': 0x11,
    'alt': 0x12,
    'a': 0x41,
    'b': 0x42,
    'c': 0x43,
    'd': 0x44,
    'e': 0x45,
    'f': 0x46,
    'g': 0x47,
    'h': 0x48,
    'i': 0x49,
    'j': 0x4A,
    'k': 0x4B,
    'l': 0x4C,
    'm': 0x4D,
    'n': 0x4E,
    'o': 0x4F,
    'p': 0x50,
    'q': 0x51,
    'r': 0x52,
    's': 0x53,
    't': 0x54,
    'u': 0x55,
    'v': 0x56,
    'w': 0x57,
    'x': 0x58,
    'y': 0x59,
    'z': 0x5A,
    '0': 0x30,
    '1': 0x31,
    '2': 0x32,
    '3': 0x33,
    '4': 0x34,
    '5': 0x35,
    '6': 0x36,
    '7': 0x37,
    '8': 0x38,
    '9': 0x39,
    'space': 0x20
}

def is_key_pressed_flag_set(key_state):
    KEY_PRESSED_FLAG = 2 ** 15
    return (key_state & KEY_PRESSED_FLAG) != 0

def is_key_pressed(vk_code):
    key_state = ctypes.windll.user32.GetAsyncKeyState(vk_code)
    return is_key_pressed_flag_set(key_state)

def are_keys_pressed(required_keys):
    return all(is_key_pressed(vk_code) for vk_code in required_keys)

class AutoClicker(QThread):
    finished = pyqtSignal()

    def __init__(self, target_keys, mouse_button, click_interval_seconds):
        super().__init__()
        self.target_keys = target_keys
        self.mouse_button = mouse_button
        self.click_interval_seconds = click_interval_seconds
        self.is_running = False

    def run(self):
        self.is_running = True
        while self.is_running:
            if are_keys_pressed(self.target_keys):
                self.auto_click()
            time.sleep(self.click_interval_seconds)

    def stop(self):
        self.is_running = False
        self.finished.emit()

    def auto_click(self):
        if self.mouse_button == 1:
            mouse.click("right")
        elif self.mouse_button == 0:
            mouse.click("left")

class AutoClickerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

        self.target_keys = []
        self.mouse_button = 0
        self.clicks_per_second = 20

        self.auto_clicker_thread = None
        self.clicker_active = False

    def init_ui(self):
        self.setWindowTitle("Автокликер")
        self.setGeometry(100, 100, 400, 250)

        layout = QVBoxLayout()

        # Заголовок
        self.label_title = QLabel("Настройка автокликера", self)
        self.label_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_title)

        # Ввод комбинации клавиш
        self.label_hotkey = QLabel("Комбинация клавиш (например, ctrl shift a):", self)
        layout.addWidget(self.label_hotkey)

        self.hotkey_input = QLineEdit(self)
        layout.addWidget(self.hotkey_input)

        # Радиокнопки для выбора кнопки мыши
        self.label_mouse_button = QLabel("Кнопка мыши:")
        layout.addWidget(self.label_mouse_button)

        radio_layout = QHBoxLayout()
        self.radio_left = QRadioButton("Левая")
        self.radio_left.setChecked(True)
        self.radio_right = QRadioButton("Правая")
        radio_layout.addWidget(self.radio_left)
        radio_layout.addWidget(self.radio_right)
        layout.addLayout(radio_layout)

        # Ввод количества кликов в секунду
        self.label_clicks_per_second = QLabel("Клики в секунду:", self)
        layout.addWidget(self.label_clicks_per_second)

        self.clicks_input = QLineEdit(self)
        self.clicks_input.setText("20")
        layout.addWidget(self.clicks_input)

        # Кнопка для запуска/остановки автокликера
        self.start_stop_button = QPushButton("Запустить", self)
        self.start_stop_button.setStyleSheet("background-color: green; color: white;")
        self.start_stop_button.clicked.connect(self.toggle_clicker)
        layout.addWidget(self.start_stop_button)

        self.setLayout(layout)

    def toggle_clicker(self):
        if self.clicker_active:
            self.stop_clicker()
        else:
            self.start_clicker()

    def start_clicker(self):
        # Проверка ввода клавиш
        hotkey_list = self.hotkey_input.text().lower().split()
        vk_codes = [VK_CODE.get(hk) for hk in hotkey_list if VK_CODE.get(hk) is not None]
        if len(vk_codes) != len(hotkey_list):
            QMessageBox.critical(self, "Ошибка", "Некорректный ввод клавиш")
            return
        self.target_keys = vk_codes

        # Получение кнопки мыши
        self.mouse_button = 0 if self.radio_left.isChecked() else 1

        # Получение количества кликов в секунду
        try:
            self.clicks_per_second = int(self.clicks_input.text())
            if self.clicks_per_second <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.critical(self, "Ошибка", "Некорректное количество кликов в секунду")
            return

        click_interval_seconds = 1 / self.clicks_per_second

        # Запуск автокликера в отдельном потоке
        self.auto_clicker_thread = AutoClicker(self.target_keys, self.mouse_button, click_interval_seconds)
        self.auto_clicker_thread.start()

        # Обновление интерфейса кнопки
        self.start_stop_button.setText("Закрыть")
        self.start_stop_button.setStyleSheet("background-color: red; color: white;")
        self.clicker_active = True

    def stop_clicker(self):
        if self.auto_clicker_thread:
            self.auto_clicker_thread.stop()
            self.auto_clicker_thread = None

        # Обновление интерфейса кнопки
        self.start_stop_button.setText("Запустить")
        self.start_stop_button.setStyleSheet("background-color: green; color: white;")
        self.clicker_active = False

    def closeEvent(self, event):
        if self.auto_clicker_thread and self.auto_clicker_thread.is_running:
            self.auto_clicker_thread.stop()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = AutoClickerApp()
    main_window.show()
    sys.exit(app.exec_())
