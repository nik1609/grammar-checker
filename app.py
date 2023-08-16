import sys
from configparser import ConfigParser
from openai_playground import OpenAIPlayground, GPT3_MODELS
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QSlider, QTabWidget, QTextEdit, QComboBox, QToolButton, QStatusBar, QHBoxLayout, QVBoxLayout, QFormLayout)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QEvent
from PyQt6.QtGui import QIcon

class TabManager(QTabWidget):
    plusClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tabBar().installEventFilter(self)
        self.setTabsClosable(True)

        self.add_button = QToolButton(self, text='+')
        self.add_button.clicked.connect(self.plusClicked)
        self.tabCloseRequested.connect(self.closeTab)
    
    def closeTab(self, tab_index):
        if self.count() == 1:
            return
        self.removeTab(tab_index)

    def eventFilter(self, obj, event):
        if obj is self.tabBar() and event.type() == QEvent.Type.Resize:
            r = self.tabBar().geometry()
            h = r.height()
            self.add_button.setFixedSize((h - 1.5) * QSize(1, 1))
            self.add_button.move(r.right() - 6, 1)
        return super().eventFilter(obj, event)

class GrammarChecker(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.openai_playground = OpenAIPlayground(API_KEY)

        self.layout = QVBoxLayout(self)
        self.init_ui()

    def init_ui(self):
        self.layout_inputs = QFormLayout()
        self.layout.addLayout(self.layout_inputs)

        self.model = QComboBox()
        self.prompt = QTextEdit()
        self.output = QTextEdit()

        self.max_tokens = QSlider(Qt.Orientation.Horizontal, minimum=10, maximum=4000, singleStep=500, pageStep=500)
        self.temperature = QSlider(Qt.Orientation.Horizontal, minimum=0, maximum=100)
        self.btn_submit = QPushButton('&Submit', clicked=self.submit)
        self.btn_reset = QPushButton("&Reset", clicked=self.reset_fields)
        self.status = QStatusBar()

        self.layout_inputs.addRow(QLabel('Model'), self.model)

        self.max_token_value = QLabel("0.0")
        self.layout_slider_max_tokens = QHBoxLayout()
        self.layout_slider_max_tokens.addWidget(self.max_token_value)
        self.layout_slider_max_tokens.addWidget(self.max_tokens)
        self.layout_inputs.addRow('Max Token:', self.layout_slider_max_tokens)

        self.temperature_value = QLabel("0.0")
        self.layout_slider_temperature = QHBoxLayout()
        self.layout_slider_temperature.addWidget(self.temperature_value)
        self.layout_slider_temperature.addWidget(self.temperature)
        self.layout_inputs.addRow('Temperature:', self.layout_slider_temperature)

        self.layout_inputs.addRow(QLabel('Prompt:'), self.prompt)
        self.layout_inputs.addRow(QLabel('Output:'), self.output)
        self.layout_inputs.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.layout_buttons = QHBoxLayout()
        self.layout.addLayout(self.layout_buttons)

        self.layout_buttons.addWidget(self.btn_submit)
        self.layout_buttons.addWidget(self.btn_reset)
        self.layout.addWidget(self.status)

        self.init_set_default_settings()
        self.init_configure_signals()

    def init_set_default_settings(self):
        self.model.addItems(['Davinci', 'Curie', 'Babbage', 'Ada'])

        self.max_tokens.setTickPosition(QSlider.TickPosition.TicksBelow)  # Corrected value
        self.max_tokens.setTickInterval(500)
        self.max_tokens.setTracking(True)
        self.max_token_value.setText('{0:,}'.format(self.max_tokens.value()))

        self.temperature.setTickPosition(QSlider.TickPosition.TicksBelow)  # Corrected value
        self.temperature.setTickInterval(10)
        self.temperature.setTracking(True)
        self.temperature_value.setText('{0:.2f}'.format(self.temperature.value()))
        

    def init_configure_signals(self):
        self.max_tokens.valueChanged.connect(lambda: self.max_token_value.setText('{0:,}'.format(self.max_tokens.value())))
        self.temperature.valueChanged.connect(lambda: self.temperature_value.setText('{0:.2f}'.format(self.temperature.value() / 100)))
    
    def reset_fields(self):
        self.prompt.clear()
        self.output.clear()
        self.status.clearMessage()

    def submit(self):
        text_block = self.prompt.toPlainText()
        if not text_block:
            self.status.showMessage('Prompt is empty.')
            return
        else:
            self.status.clearMessage()
        self.output.clear()
        prompt = 'Check the grammar for the following sentence:\n{0}'.format(text_block.strip())
        model = GPT3_MODELS[self.model.currentText().lower()]
        temperature = float('{0:.2f}'.format(self.temperature.value() / 100))

        try:
            response = self.openai_playground.grammar_checker(prompt, max_tokens=self.max_tokens.value(), temperature=temperature)
            self.output.setPlainText(response.get('outputs').strip())
            self.status.showMessage('Tokens used: {0}'.format(response.get('total_tokens')))
        except Exception as e:
            self.status.showMessage(str(e))

class AppWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.window_width, self.window_height = 700, 500
        self.setMinimumSize(self.window_width, self.window_height)
        self.setWindowIcon(QIcon("chatgpt.png"))
        self.setWindowTitle("Grammar checker by OpenAi")
        self.setStyleSheet('''
            QWidget {
            font-size: 14px;
            }
        ''')
        self.layout = QVBoxLayout(self)
        self.init_ui()
        self.init_configure_signal()

    def init_ui(self):
        self.tab_manager = TabManager(self)
        self.layout.addWidget(self.tab_manager)

        self.tab_manager.addTab(GrammarChecker(), 'Grammar Checker #1')
        
    def add_tab(self):
        tab_count = self.tab_manager.count() + 1
        self.tab_manager.addTab(GrammarChecker(), 'Grammar Checker #{0}'.format(tab_count))

    def init_configure_signal(self):
        self.tab_manager.plusClicked.connect(self.add_tab)

if __name__ == "__main__":
    config = ConfigParser()
    config.read("password_manager.ini")
    API_KEY = config.get('openai', 'API_KEY')

    app = QApplication(sys.argv)
    w = AppWindow()
    w.show()
    sys.exit(app.exec())
