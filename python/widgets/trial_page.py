"""Trial page: live recording for one pivot configuration.

Shows: pendulum widget, real-time Angle plot, real-time Gyro plot,
swing counter, running period averages, and post-trial stopwatch entry.
"""

import numpy as np
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

from widgets.pendulum_widget import PendulumWidget
from data_processor import DataProcessor, Method

WINDOW_SIZE = 400  # scrolling plot width in samples (4 seconds at 100 Hz)


class TrialPage(QtWidgets.QWidget):
    """Recording page for one pivot trial.
    
    Signals:
        trial_accepted(dict) - emitted when user accepts results.
        trial_redo()         - emitted when user wants to redo.
    """
    trial_accepted = QtCore.pyqtSignal(dict)
    trial_redo = QtCore.pyqtSignal()
    recording_started = QtCore.pyqtSignal()
    recording_stopped = QtCore.pyqtSignal()

    def __init__(self, pivot_name: str = "Pivot 1", parent=None):
        super().__init__(parent)
        self.pivot_name = pivot_name
        self.processor: DataProcessor = None

        layout = QtWidgets.QVBoxLayout(self)

        # Title
        title = QtWidgets.QLabel(f"Step - {pivot_name} Trial")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #00d2ff;")
        layout.addWidget(title)

        # ── Top row: pendulum + live graphs ──────────
        top = QtWidgets.QHBoxLayout()

        # Pendulum 2D visualizer
        self.pendulum = PendulumWidget()
        self.pendulum.setMinimumSize(360, 360)
        top.addWidget(self.pendulum, stretch=1)

        # Graphs: Angle plot + Gyro plot + Decay plot
        plots = pg.GraphicsLayoutWidget()
        
        # 1. Live Angle Plot (degrees)
        self.angle_plot = plots.addPlot(title="Live Pendulum Tilt Angle θ (deg)")
        self.angle_plot.showGrid(x=True, y=True, alpha=0.3)
        self.angle_plot.setYRange(-60, 60)
        self.angle_plot.addLine(y=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
        self.angle_curve = self.angle_plot.plot(pen=pg.mkPen('#00ff88', width=2))

        plots.nextRow()

        # 2. Live Angular Velocity Plot (deg/s)
        self.gyro_plot = plots.addPlot(title="Angular Velocity ω (°/s) & Reversal Points")
        self.gyro_plot.showGrid(x=True, y=True, alpha=0.3)
        self.gyro_curve = self.gyro_plot.plot(pen=pg.mkPen('#00d2ff', width=2))
        self.gyro_plot.addLine(y=0, pen=pg.mkPen('w', width=1, style=QtCore.Qt.DashLine))
        self.gyro_crossing_dots = pg.ScatterPlotItem(pen=None, brush='r', size=8)
        self.gyro_plot.addItem(self.gyro_crossing_dots)
        self.ir_crossing_dots = pg.ScatterPlotItem(pen=None, brush='#ffcc00', size=9, symbol='d')
        self.gyro_plot.addItem(self.ir_crossing_dots)

        plots.nextRow()

        # 3. Peak Amplitude Decay Plot
        self.decay_plot = plots.addPlot(title="Peak Amplitude Decay per Swing (°)")
        self.decay_plot.showGrid(x=True, y=True, alpha=0.3)
        self.decay_scatter = pg.ScatterPlotItem(pen=None, brush='#ff6b6b', size=6)
        self.decay_plot.addItem(self.decay_scatter)
        self.decay_fit = self.decay_plot.plot(pen=pg.mkPen('#00ff88', width=2, style=QtCore.Qt.DashLine))

        top.addWidget(plots, stretch=2)
        layout.addLayout(top)

        # ── Control bar ─────────────────────────────
        ctrl = QtWidgets.QHBoxLayout()

        ctrl.addWidget(QtWidgets.QLabel("Mount Orientation:"))
        self.orient_combo = QtWidgets.QComboBox()
        self.orient_combo.addItem("Auto-Detect Orientation", "auto")
        self.orient_combo.addItem("Flat on Rod (Z along rod, Gyro Y)", "flat_z")
        self.orient_combo.addItem("Vertical / Header Up (Y along rod, Gyro Z)", "vertical_y")
        self.orient_combo.addItem("Side Mount (Z along rod, Gyro X)", "side_x")
        self.orient_combo.currentIndexChanged.connect(self._on_orient_changed)
        ctrl.addWidget(self.orient_combo)

        ctrl.addSpacing(20)

        self.cal_btn = QtWidgets.QPushButton("📐 Calibrate Zero (hang still)")
        self.cal_btn.setStyleSheet("padding: 10px; font-size: 14px; font-weight: bold;")
        ctrl.addWidget(self.cal_btn)

        self.start_btn = QtWidgets.QPushButton("▶ Start Recording")
        self.start_btn.setStyleSheet("padding: 10px; font-size: 14px; font-weight: bold; background: #00cc66; color: #111;")
        self.start_btn.setEnabled(True)  # allow immediate recording once connected
        ctrl.addWidget(self.start_btn)

        self.stop_btn = QtWidgets.QPushButton("⏹ Stop Recording")
        self.stop_btn.setStyleSheet("padding: 10px; font-size: 14px; font-weight: bold; background: #ff4444; color: white;")
        self.stop_btn.setEnabled(False)
        ctrl.addWidget(self.stop_btn)

        layout.addLayout(ctrl)

        # ── Live stats bar ──────────────────────────
        stats = QtWidgets.QHBoxLayout()
        self.lbl_live_theta = self._stat_label("Current θ: 0.0°")
        self.lbl_swings = self._stat_label("Swings: 0")
        self.lbl_T_gyro = self._stat_label("T (gyro): —")
        self.lbl_T_ir = self._stat_label("T (IR): —")
        self.lbl_peak_theta = self._stat_label("Peak θ₀: —")
        self.lbl_status = self._stat_label("Status: Live Preview")
        for lbl in [self.lbl_live_theta, self.lbl_swings, self.lbl_T_gyro,
                     self.lbl_T_ir, self.lbl_peak_theta, self.lbl_status]:
            stats.addWidget(lbl)
        layout.addLayout(stats)

        # ── Post-trial: stopwatch entry + accept/redo ──
        self.post_frame = QtWidgets.QGroupBox("Manual Stopwatch Comparison (Ground Truth / Baseline)")
        self.post_frame.setVisible(False)
        post_layout = QtWidgets.QFormLayout(self.post_frame)

        self.sw_N = QtWidgets.QSpinBox()
        self.sw_N.setRange(1, 500)
        self.sw_N.setValue(20)
        post_layout.addRow("Oscillations timed manually:", self.sw_N)

        self.sw_time = QtWidgets.QDoubleSpinBox()
        self.sw_time.setRange(0, 9999)
        self.sw_time.setDecimals(2)
        self.sw_time.setSuffix(" s")
        post_layout.addRow("Stopwatch total time:", self.sw_time)

        self.sw_result = QtWidgets.QLabel("T = — s")
        self.sw_result.setStyleSheet("font-weight: bold; color: #00d2ff;")
        post_layout.addRow("Manual T per oscillation:", self.sw_result)
        self.sw_time.valueChanged.connect(self._update_manual_T)
        self.sw_N.valueChanged.connect(self._update_manual_T)

        btn_row = QtWidgets.QHBoxLayout()
        self.accept_btn = QtWidgets.QPushButton("✅ Accept & Continue")
        self.accept_btn.setStyleSheet("padding: 10px 20px; font-size: 14px; font-weight: bold; background: #00d2ff; color: #111;")
        self.redo_btn = QtWidgets.QPushButton("🔄 Redo Trial")
        self.redo_btn.setStyleSheet("padding: 10px 20px; font-size: 14px;")
        btn_row.addWidget(self.accept_btn)
        btn_row.addWidget(self.redo_btn)
        post_layout.addRow(btn_row)

        layout.addWidget(self.post_frame)

        # ── Wire buttons ────────────────────────────
        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn.clicked.connect(self._on_stop)
        self.accept_btn.clicked.connect(self._on_accept)
        self.redo_btn.clicked.connect(self._on_redo)

        # ── Internal state ──────────────────────────
        self.angle_buf = np.zeros(WINDOW_SIZE)
        self.gyro_buf = np.zeros(WINDOW_SIZE)
        self._recording = False
        self._gyro_crossing_positions = []
        self._ir_crossing_positions = []
        self._sample_count = 0
        self.detected_orientation = "flat_z"

    def _stat_label(self, text):
        lbl = QtWidgets.QLabel(text)
        lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #e0e0e0; padding: 4px 8px; background: #1c1c30; border-radius: 4px;")
        return lbl

    def set_orientation(self, orient: str):
        self.detected_orientation = orient
        if orient == "vertical_y":
            rod_axis, perp_axis, gyro_axis = 'ay', 'ax', 'gz'
        elif orient == "side_x":
            rod_axis, perp_axis, gyro_axis = 'ax', 'ay', 'gz'
        else:  # flat_z
            rod_axis, perp_axis, gyro_axis = 'az', 'ax', 'gy'

        if self.processor:
            self.processor.accel_rod_axis = rod_axis
            self.processor.accel_perp_axis = perp_axis
            self.processor.gyro_axis = gyro_axis

    def _on_orient_changed(self):
        choice = self.orient_combo.currentData()
        if choice != "auto":
            self._orientation_locked = True
            self.set_orientation(choice)

    def set_calibrated(self):
        self._orientation_locked = True
        self.start_btn.setEnabled(True)
        self.lbl_status.setText("Status: Calibrated ✅")
        self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ff88; padding: 4px 8px; background: #1c1c30; border-radius: 4px;")

    def _on_start(self):
        self._recording = True
        self.post_frame.setVisible(False)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.cal_btn.setEnabled(False)
        self.pendulum.reset_trail()
        self.angle_buf[:] = 0
        self.gyro_buf[:] = 0
        self._gyro_crossing_positions.clear()
        self._ir_crossing_positions.clear()
        self._sample_count = 0
        if self.processor:
            self.processor.start_recording()
        self.lbl_status.setText("Status: ● RECORDING")
        self.lbl_status.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #ff4444; padding: 4px 8px; background: #1c1c30; border-radius: 4px;")
        self.recording_started.emit()

    def _on_stop(self):
        self._recording = False
        self.stop_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        self.cal_btn.setEnabled(True)
        if self.processor:
            self.processor.stop_recording()
        self.post_frame.setVisible(True)
        self.lbl_status.setText("Status: Stopped — Enter Stopwatch Time")
        self.lbl_status.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #ffaa00; padding: 4px 8px; background: #1c1c30; border-radius: 4px;")
        self.recording_stopped.emit()

    def _update_manual_T(self):
        N = self.sw_N.value()
        t = self.sw_time.value()
        if N > 0 and t > 0:
            self.sw_result.setText(f"T = {t / N:.5f} s")

    def _on_accept(self):
        N = self.sw_N.value()
        t = self.sw_time.value()
        self.trial_accepted.emit({
            'processor': self.processor,
            'manual_T': t if t > 0 else None,
            'manual_N': N if t > 0 else None,
        })

    def _on_redo(self):
        self.start_btn.setEnabled(True)
        self.post_frame.setVisible(False)
        self.lbl_status.setText("Status: Ready to redo")
        self.trial_redo.emit()

    def _calculate_angle_and_gyro(self, sample: dict):
        ax, ay, az = sample['ax'], sample['ay'], sample['az']
        gx, gy, gz = sample['gx'], sample['gy'], sample['gz']

        mode = self.orient_combo.currentData()
        if mode == "auto":
            # Auto-detect which axis is aligned with gravity
            if abs(ay) > abs(az) and abs(ay) > 0.5:
                # Board is held vertically (Y along rod)
                theta = np.arctan2(ax, abs(ay))
                gyro = gz
                active_orient = "vertical_y"
            elif abs(ax) > abs(az) and abs(ax) > 0.5:
                theta = np.arctan2(ay, abs(ax))
                gyro = gz
                active_orient = "horizontal_x"
            else:
                # Board is flat (Z along rod)
                theta = np.arctan2(ax, abs(az))
                gyro = gy
                active_orient = "flat_z"

            if active_orient != self.detected_orientation:
                self.detected_orientation = active_orient
                if self.processor:
                    if active_orient == "vertical_y":
                        self.processor.gyro_axis = 'gz'
                        self.processor.accel_rod_axis = 'ay'
                    else:
                        self.processor.gyro_axis = 'gy'
                        self.processor.accel_rod_axis = 'az'
        elif mode == "vertical_y":
            theta = np.arctan2(ax, abs(ay) if abs(ay) > 0.05 else 1.0)
            gyro = gz
        elif mode == "side_x":
            theta = np.arctan2(ay, abs(az) if abs(az) > 0.05 else 1.0)
            gyro = gx
        else:  # flat_z
            theta = np.arctan2(ax, abs(az) if abs(az) > 0.05 else 1.0)
            gyro = gy

        return float(theta), float(gyro)

    def process_and_draw(self, sample: dict):
        """Called from the main update loop with each new sample."""
        if not self.processor:
            return

        # Initial one-time orientation lock if set to auto and not yet locked
        if not getattr(self, '_orientation_locked', False) and self.orient_combo.currentData() == "auto":
            ay = sample.get('ay', 0.0)
            az = sample.get('az', 1.0)
            ax = sample.get('ax', 0.0)
            abs_axes = {'vertical_y': abs(ay), 'flat_z': abs(az), 'side_x': abs(ax)}
            best = max(abs_axes, key=abs_axes.get)
            self.set_orientation(best)
            self._orientation_locked = True

        # Fused sensor processing (runs complementary filter continuously)
        self.processor.process_sample(sample)
        self._sample_count += 1

        theta_rad = self.processor.current_angle_rad
        theta_deg = self.processor.current_angle_deg
        gyro_deg = float(np.degrees(self.processor.current_omega_rad))

        # Always update 2D pendulum animation using smooth fused angle
        self.pendulum.update_pendulum(theta_rad, gyro_deg)

        # Update real-time scrolling Angle plot
        self.angle_buf = np.roll(self.angle_buf, -1)
        self.angle_buf[-1] = theta_deg
        self.angle_curve.setData(self.angle_buf)

        # Update real-time scrolling Gyro plot
        self.gyro_buf = np.roll(self.gyro_buf, -1)
        self.gyro_buf[-1] = gyro_deg
        self.gyro_curve.setData(self.gyro_buf)

        # Continuous live angle display
        self.lbl_live_theta.setText(f"Current θ: {theta_deg:+.1f}°")

        if not self._recording:
            return

        # Track crossing positions for scatter markers
        n_swings_now = len(self.processor.swings)
        if n_swings_now > len(self._gyro_crossing_positions):
            self._gyro_crossing_positions.append(self._sample_count)
            positions = [WINDOW_SIZE - (self._sample_count - p)
                         for p in self._gyro_crossing_positions
                         if self._sample_count - p < WINDOW_SIZE]
            valid_pos = [p for p in positions if 0 <= p < WINDOW_SIZE]
            self.gyro_crossing_dots.setData(
                valid_pos,
                [0] * len(valid_pos)
            )

        n_ir_now = len(self.processor.ir_crossings)
        if n_ir_now > len(self._ir_crossing_positions):
            self._ir_crossing_positions.append(self._sample_count)
            ir_positions = [WINDOW_SIZE - (self._sample_count - p)
                            for p in self._ir_crossing_positions
                            if self._sample_count - p < WINDOW_SIZE]
            valid_ir = [p for p in ir_positions if 0 <= p < WINDOW_SIZE]
            self.ir_crossing_dots.setData(
                valid_ir,
                [0] * len(valid_ir)
            )

        # Live stats
        self.lbl_swings.setText(f"Swings: {n_swings_now}")
        if self.processor.swings:
            self.lbl_peak_theta.setText(
                f"Peak θ₀: {self.processor.swings[-1].amplitude_deg:.1f}°")
        T_g, _ = self.processor.get_mean_period(Method.GYRO)
        if T_g:
            self.lbl_T_gyro.setText(f"T (gyro): {T_g:.5f} s")
        T_ir, _ = self.processor.get_mean_period(Method.IR)
        if T_ir:
            self.lbl_T_ir.setText(f"T (IR): {T_ir:.5f} s")

        # Decay scatter
        sn, sa = self.processor.get_decay_data()
        if len(sn) > 0:
            self.decay_scatter.setData(sn, sa)
