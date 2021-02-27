import sys
import time
import threading

from pydub import AudioSegment
from pydub.playback import play

import PyQt5
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QLabel, QHBoxLayout, QVBoxLayout, QWidget, QPushButton, QProgressBar
from PyQt5.QtGui import QIcon, QPixmap, QMovie

from PyQt5.QtCore import Qt, QByteArray, QSettings, QTimer, pyqtSlot
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QSizePolicy, QVBoxLayout, QAction, QPushButton
from PyQt5.QtGui import QMovie

class STATE():
    WORK = 1
    PAUSE = 2

CYCLE_LENGTHS = {
        STATE.WORK: 25*60,
        STATE.PAUSE: 5*60,
        # STATE.WORK: 15,
        # STATE.PAUSE: 5,
        }
STATE_LABELS = {
        STATE.WORK: 'Work',
        STATE.PAUSE: 'Break',
        }

class CloseableQWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.loop_stopper = None

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Q:
            self.close()
    def closeEvent(self, e):
        if self.loop_stopper is not None:
            self.loop_stopper.set()

class Pomodoro():

    def __init__(self):
        self.timer = 0
        self.progress_value = 0
        self.running = False
        self.cycles = 0
        self.state = STATE.WORK
        self.beep = AudioSegment.from_mp3("pomodoro.mp3")

    def swap_state(self):
        if self.state == STATE.WORK:
            self.state = STATE.PAUSE
        else:
            self.state = STATE.WORK
            self.cycles += 1
            self.set_cycles()

    def swap(self):
        self.swap_state()
        self.state_label.setText(STATE_LABELS[self.state])
        self.timer = 0
        play(self.beep)

    def reset(self):
        self.timer = 0
        self.change_progress_bar()
        self.change_time_label()

    def toggle(self):
        if self.running:
            self.toggle_button.setText('Play')
            self.running = False
            self.loop_stopper.set()
            self.movie.stop()
        else:
            self.toggle_button.setText('Pause')
            self.running = True
            self.run()
            self.movie.start()

    def set_cycles(self):
        self.cycles_label.setText('{} cycles'.format(self.cycles))

    def run(self):
        self.loop_stopper = threading.Event()
        self.window.loop_stopper = self.loop_stopper
        self.loop = threading.Thread(target=self.clock_loop, args=(self.loop_stopper,))
        self.loop.start()

    def change_progress_bar(self):
        new_progress_value = int(self.timer / CYCLE_LENGTHS[self.state] * 100)
        if new_progress_value != self.progress_value:
            self.progress_value = new_progress_value
            self.progress.setValue(self.progress_value)

    def change_time_label(self):
        mins = self.timer // 60
        secs = self.timer - mins*60
        total_mins = CYCLE_LENGTHS[self.state] // 60
        total_secs = CYCLE_LENGTHS[self.state] - total_mins*60
        new_time_label = "{:02d}:{:02d} / {:02d}:{:02d}".format(mins, secs, total_mins, total_secs)
        self.time_label.setText(new_time_label)

    def clock_loop(self, stopper):
        while not stopper.isSet():
            self.timer += 1
            self.change_progress_bar()
            self.change_time_label()
            if self.timer == CYCLE_LENGTHS[self.state]:
                self.swap()
            time.sleep(1)

    def exec(self):
        self.app = QApplication([])

        # button font
        button_font = QtGui.QFont("Sans", 13, QtGui.QFont.Bold)

        # toggle button
        self.toggle_button = QPushButton('Start')
        self.toggle_button.setCheckable(True)
        self.toggle_button.clicked.connect(self.toggle)
        self.toggle_button.setFont(button_font)

        # reset button
        self.reset_button = QPushButton('Reset')
        self.reset_button.clicked.connect(self.reset)
        self.reset_button.setFont(button_font)

        # progress label
        self.progress_label = QLabel()
        self.movie = QMovie("spinner.gif")
        self.progress_label.setMovie(self.movie)
        self.progress_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.progress_label.setAlignment(Qt.AlignCenter)

        # label
        self.label = QLabel('Pomodoro timer')
        self.pixmap = QPixmap('pomodoro.png')
        self.label.setPixmap(self.pixmap)

        # time label
        self.time_label = QLabel('00:00 / 25:00')
        self.time_label.setFont(button_font)

        # cycles label
        self.cycles_label = QLabel('0 cycles')
        cycles_font = QtGui.QFont("Sans", 12, QtGui.QFont.Bold)
        self.cycles_label.setFont(cycles_font)

        # state label
        state_font = QtGui.QFont("Sans", 18, QtGui.QFont.Bold)
        self.state_label = QLabel(STATE_LABELS[self.state])
        self.state_label.setFont(state_font)

        # progressbar
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setMinimum(0)
        self.progress.setValue(0)

        self.window = CloseableQWidget()
        self.window.setGeometry(770, 440, 400, 200)

        self.outer_vertical = QVBoxLayout()
        self.inner_horizonal = QHBoxLayout()
        self.buttons_vertical = QVBoxLayout()
        self.slider_clock_layout = QHBoxLayout()
        self.labels = QHBoxLayout()

        self.outer_vertical.addLayout(self.inner_horizonal)

        self.inner_horizonal.addWidget(self.label)
        self.inner_horizonal.addLayout(self.buttons_vertical)

        self.buttons_vertical.addWidget(self.toggle_button)
        self.buttons_vertical.addWidget(self.reset_button)

        self.slider_clock_layout.addWidget(self.progress)
        self.slider_clock_layout.addWidget(self.time_label)

        self.labels.addWidget(self.state_label)
        self.labels.addWidget(self.cycles_label)
        self.labels.addWidget(self.progress_label, alignment=Qt.AlignRight)
        self.outer_vertical.addLayout(self.labels)
        self.outer_vertical.addLayout(self.slider_clock_layout)

        self.window.setLayout(self.outer_vertical)
        self.window.show()

        # gif options
        self.movie.setCacheMode(QMovie.CacheAll)
        self.progress_label.setMovie(self.movie)
        self.movie.jumpToFrame(1)
        self.movie.loopCount()

        self.app.setStyle('Fusion')
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    Pomodoro().exec()
    print('exits')

