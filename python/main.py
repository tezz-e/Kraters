"""Kater's Pendulum Experiment — Main Application.

Launches a wizard-style UI: Setup -> Pivot 1 -> Pivot 2 -> Results.
"""

import sys
import os
import queue
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui

from serial_reader import SerialReader
from data_processor import DataProcessor
from data_logger import DataLogger
from experiment import Experiment

from widgets.setup_page import SetupPage
from widgets.trial_page import TrialPage
from widgets.results_page import ResultsPage


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kater's Pendulum — Experiment System")
        self.resize(1400, 900)

        self.reader: SerialReader = None
        self.experiment = Experiment()
        self.logger = DataLogger()
        self._current_processor: DataProcessor = None

        # ── Wizard pages ────────────────────────────
        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        self.setup_page = SetupPage()
        self.trial1_page = TrialPage("Pivot 1")
        self.trial2_page = TrialPage("Pivot 2")
        self.results_page = ResultsPage()

        # Initialize default processor
        proc_init = DataProcessor(a_rest=1.0, gyro_axis='gy', accel_rod_axis='az', accel_perp_axis='ax')
        self.trial1_page.processor = proc_init
        self.trial2_page.processor = proc_init
        self._current_processor = proc_init

        self.stack.addWidget(self.setup_page)    # index 0
        self.stack.addWidget(self.trial1_page)   # index 1
        self.stack.addWidget(self.trial2_page)   # index 2
        self.stack.addWidget(self.results_page)  # index 3

        # ── Wire signals ────────────────────────────
        self.setup_page.connect_btn.clicked.connect(self._connect_esp)
        self.setup_page.proceed.connect(self._go_to_trial1)

        self.trial1_page.cal_btn.clicked.connect(self._calibrate)
        self.trial1_page.trial_accepted.connect(self._trial1_done)
        self.trial1_page.trial_redo.connect(self._trial1_redo)
        self.trial1_page.recording_started.connect(lambda: self.logger.start_csv("pivot1"))
        self.trial1_page.recording_stopped.connect(self.logger.stop_csv)

        self.trial2_page.cal_btn.clicked.connect(self._calibrate)
        self.trial2_page.trial_accepted.connect(self._trial2_done)
        self.trial2_page.trial_redo.connect(self._trial2_redo)
        self.trial2_page.recording_started.connect(lambda: self.logger.start_csv("pivot2"))
        self.trial2_page.recording_stopped.connect(self.logger.stop_csv)

        self.results_page.export_csv_btn.clicked.connect(self._export_csv)
        self.results_page.export_json_btn.clicked.connect(self._export_json)

        # ── Update timer ────────────────────────────
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._update)
        self.timer.start(25)  # 40 FPS

    def _connect_esp(self):
        port = self.setup_page.get_port()
        self.reader = SerialReader(port)
        success = self.reader.connect()
        self.setup_page.set_connected(success)
        if success:
            self.reader.start()
            params = self.setup_page.get_params()
            self.experiment.L = params['L']
            self.experiment.h1_minus_h2 = params['h1_minus_h2']
            self.experiment.g_accepted = params['g_accepted']

    def _calibrate(self):
        if self.reader:
            page = self.trial1_page if self.stack.currentIndex() == 1 else self.trial2_page
            page.lbl_status.setText("Status: Calibrating... keep pendulum still")
            page.lbl_status.setStyleSheet(
                "font-size: 14px; font-weight: bold; color: #ffaa00; padding: 4px 8px; background: #1c1c30; border-radius: 4px;")
            page.cal_btn.setEnabled(False)
            self.reader.send_command("CMD:CAL")

    def _check_calibration(self):
        if self.stack.currentIndex() not in (1, 2):
            return
        page = self.trial1_page if self.stack.currentIndex() == 1 else self.trial2_page
        if self.reader and self.reader.a_rest is not None:
            dominant = getattr(self.reader, 'dominant_axis', 'az')
            if page.orient_combo.currentData() == "auto":
                if dominant == 'ay':
                    page.set_orientation("vertical_y")
                elif dominant == 'ax':
                    page.set_orientation("side_x")
                else:
                    page.set_orientation("flat_z")

            if self._current_processor:
                self._current_processor.accel_rod_axis = page.processor.accel_rod_axis
                self._current_processor.accel_perp_axis = page.processor.accel_perp_axis
                self._current_processor.gyro_axis = page.processor.gyro_axis
                self._current_processor.set_rest_calibration(
                    self.reader.a_rest,
                    getattr(self.reader, 'a_perp_rest', 0.0)
                )
            page.set_calibrated()
            page.cal_btn.setEnabled(True)

    def _go_to_trial1(self):
        dominant = getattr(self.reader, 'dominant_axis', 'az') if self.reader else 'az'
        a_rest_val = self.reader.a_rest if (self.reader and self.reader.a_rest) else 1.0
        a_perp_val = getattr(self.reader, 'a_perp_rest', 0.0) if self.reader else 0.0

        if self.trial1_page.orient_combo.currentData() == "auto":
            if dominant == 'ay':
                self.trial1_page.set_orientation("vertical_y")
            elif dominant == 'ax':
                self.trial1_page.set_orientation("side_x")
            else:
                self.trial1_page.set_orientation("flat_z")

        proc = DataProcessor(
            a_rest=a_rest_val,
            gyro_axis=self.trial1_page.processor.gyro_axis,
            accel_rod_axis=self.trial1_page.processor.accel_rod_axis,
            accel_perp_axis=self.trial1_page.processor.accel_perp_axis)
        proc.set_rest_calibration(a_rest_val, a_perp_val)
        self.trial1_page.processor = proc
        self._current_processor = proc
        self.stack.setCurrentIndex(1)

    def _trial1_redo(self):
        a_rest_val = self.reader.a_rest if (self.reader and self.reader.a_rest) else 1.0
        a_perp_val = getattr(self.reader, 'a_perp_rest', 0.0) if self.reader else 0.0
        proc = DataProcessor(
            a_rest=a_rest_val,
            gyro_axis=self.trial1_page.processor.gyro_axis,
            accel_rod_axis=self.trial1_page.processor.accel_rod_axis,
            accel_perp_axis=self.trial1_page.processor.accel_perp_axis)
        proc.set_rest_calibration(a_rest_val, a_perp_val)
        self.trial1_page.processor = proc
        self._current_processor = proc

    def _trial1_done(self, data):
        proc = data['processor']
        self.experiment.trial1 = self.experiment.finalize_trial(
            proc, "Pivot 1", data.get('manual_T'), data.get('manual_N'))
        # Prepare pivot 2
        dominant = getattr(self.reader, 'dominant_axis', 'az') if self.reader else 'az'
        a_rest_val = self.reader.a_rest if (self.reader and self.reader.a_rest) else 1.0
        a_perp_val = getattr(self.reader, 'a_perp_rest', 0.0) if self.reader else 0.0

        if self.trial2_page.orient_combo.currentData() == "auto":
            if dominant == 'ay':
                self.trial2_page.set_orientation("vertical_y")
            elif dominant == 'ax':
                self.trial2_page.set_orientation("side_x")
            else:
                self.trial2_page.set_orientation("flat_z")

        proc2 = DataProcessor(
            a_rest=a_rest_val,
            gyro_axis=self.trial2_page.processor.gyro_axis,
            accel_rod_axis=self.trial2_page.processor.accel_rod_axis,
            accel_perp_axis=self.trial2_page.processor.accel_perp_axis)
        proc2.set_rest_calibration(a_rest_val, a_perp_val)
        self.trial2_page.processor = proc2
        self._current_processor = proc2
        self.trial2_page.start_btn.setEnabled(False)
        self.trial2_page.lbl_status.setText("Status: Invert Pendulum & Calibrate Zero")
        self.trial2_page.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffaa00; padding: 4px 8px; background: #1c1c30; border-radius: 4px;")
        self.stack.setCurrentIndex(2)

    def _trial2_redo(self):
        a_rest_val = self.reader.a_rest if (self.reader and self.reader.a_rest) else 1.0
        a_perp_val = getattr(self.reader, 'a_perp_rest', 0.0) if self.reader else 0.0
        proc2 = DataProcessor(
            a_rest=a_rest_val,
            gyro_axis=self.trial2_page.processor.gyro_axis,
            accel_rod_axis=self.trial2_page.processor.accel_rod_axis,
            accel_perp_axis=self.trial2_page.processor.accel_perp_axis)
        proc2.set_rest_calibration(a_rest_val, a_perp_val)
        self.trial2_page.processor = proc2
        self._current_processor = proc2

    def _trial2_done(self, data):
        proc = data['processor']
        self.experiment.trial2 = self.experiment.finalize_trial(
            proc, "Pivot 2", data.get('manual_T'), data.get('manual_N'))
        # Show results
        self.results_page.populate(self.experiment)
        self.stack.setCurrentIndex(3)

    def _export_json(self):
        results = self.experiment.compute_results()
        path = self.logger.save_session(results)
        QtWidgets.QMessageBox.information(self, "Exported",
                                          f"Results saved to:\n{path}")

    def _export_csv(self):
        csv_files = getattr(self.logger, 'saved_csvs', [])
        if csv_files:
            file_list = "\n".join(csv_files)
            QtWidgets.QMessageBox.information(
                self, "Exported Raw CSV Data",
                f"CSV data files recorded in this session:\n\n{file_list}"
            )
        else:
            QtWidgets.QMessageBox.information(
                self, "Export Raw CSV Data",
                f"Data folder: {os.path.abspath(self.logger.output_dir)}\n(No CSV recorded yet in this session)"
            )

    def _update(self):
        """Main update loop: drain serial queue, feed to current trial."""
        if not self.reader:
            return

        # Check metadata messages
        while not self.reader.meta_queue.empty():
            try:
                msg = self.reader.meta_queue.get_nowait()
                if isinstance(msg, tuple) and msg[0] == 'IR_MID':
                    t_mid = msg[1]
                    if self._current_processor:
                        self._current_processor.process_ir_midpoint(t_mid)
                elif msg == 'CAL_DONE':
                    print("[ESP] Gyro calibration complete. Sampling rest gravity...")
                elif msg == 'REST_CAL_DONE':
                    print("[ESP] Rest gravity calibration complete.")
                    self._check_calibration()
                else:
                    print(f"[ESP] {msg}")
            except queue.Empty:
                break

        # Drain data queue and feed to active page
        page_idx = self.stack.currentIndex()
        if page_idx == 0:
            last_sample = None
            while not self.reader.data_queue.empty():
                try:
                    last_sample = self.reader.data_queue.get_nowait()
                except queue.Empty:
                    break
            if last_sample:
                self.setup_page.update_preview(last_sample)
            return

        if page_idx not in (1, 2):
            while not self.reader.data_queue.empty():
                try:
                    self.reader.data_queue.get_nowait()
                except queue.Empty:
                    break
            return

        trial_page = self.trial1_page if page_idx == 1 else self.trial2_page
        while not self.reader.data_queue.empty():
            try:
                sample = self.reader.data_queue.get_nowait()
                trial_page.process_and_draw(sample)
                if trial_page._recording:
                    self.logger.write_sample(sample)
            except queue.Empty:
                break

    def closeEvent(self, event):
        self.logger.stop_csv()
        if self.reader:
            self.reader.stop()
        event.accept()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')

    # Dark palette
    pal = app.palette()
    from PyQt5.QtGui import QColor
    pal.setColor(pal.Window, QColor(26, 26, 46))
    pal.setColor(pal.WindowText, QColor(224, 224, 224))
    pal.setColor(pal.Base, QColor(15, 15, 30))
    pal.setColor(pal.Text, QColor(224, 224, 224))
    pal.setColor(pal.Button, QColor(40, 40, 70))
    pal.setColor(pal.ButtonText, QColor(224, 224, 224))
    pal.setColor(pal.Highlight, QColor(0, 210, 255))
    app.setPalette(pal)

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
