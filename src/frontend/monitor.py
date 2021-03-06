# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt

import threading, time

from ui_monitor import MonitorWidget, Ui_Form
from PersistentGeometry import PersistentGeometry


class MonitorWindow(MonitorWidget, Ui_Form, PersistentGeometry):
    sigTaskUpdating = pyqtSignal(dict)

    _stat = None
    _thread = None
    _thread_should_stop = False

    TICKS_PER_TASK = 4
    TICK_INTERVAL = 0.5  # second(s)

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)
        self.setStyleSheet("background-color: rgba(135, 206, 235, 0.8)")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)

        app.settings.applySettings.connect(self._setMonitorFullSpeed)
        self._setMonitorFullSpeed()

        self._thread = threading.Thread(target = self.updateTaskThread,
                                        name = "monitor task updating",
                                        daemon = True)
        self._thread.start()
        self.preserveGeometry("monitor")

    def updateTaskThread(self):
        while True:
            runningTaskIds = app.etmpy.runningTasksStat.getTIDs()
            if runningTaskIds:
                for tid in runningTaskIds:
                    for i in range(self.TICKS_PER_TASK):
                        task = app.etmpy.runningTasksStat.getTask(tid)

                        if self._thread_should_stop:
                            return  # end the thread

                        logging.debug("updateSpeedsThread, deadlock incoming, maybe")
                        time.sleep(self.TICK_INTERVAL)
                        try:
                            self.sigTaskUpdating.emit(task)
                        except TypeError:
                            # monitor closed
                            return  # end the thread

                        # FIXME: move the sleep function ahead, before sigTaskUpdating.emit
                        # it seems to make the deadlock go away.
                        # time.sleep(self.TICK_INTERVAL)
            else:
                time.sleep(self.TICK_INTERVAL)
                self.sigTaskUpdating.emit(dict())

    @pyqtSlot()
    def _setMonitorFullSpeed(self):
        fullSpeed = app.settings.getint("frontend", "monitorfullspeed")
        logging.info("monitor full speed -> {}".format(fullSpeed))
        self.graphicsView.FULLSPEED = 1024 * fullSpeed

    def closeEvent(self, qCloseEvent):
        self._thread_should_stop = True
        super().closeEvent(qCloseEvent)
