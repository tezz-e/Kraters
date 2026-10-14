"""Results page: final comparison dashboard.

Shows side-by-side table of Gyro vs IR vs Manual results,
computed g values, percentage errors, and export buttons.
"""

import numpy as np
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

from experiment import Experiment
from pendulum_physics import fit_decay


class ResultsPage(QtWidgets.QWidget):
    """Step 4: Final results comparison dashboard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        title = QtWidgets.QLabel("Step 4 - Results & Accuracy Comparison")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #00d2ff;")
        layout.addWidget(title)

        subtitle = QtWidgets.QLabel(
            "Comparison of automated IMU gyro zero-crossing, IR break-beam sensor, and manual stopwatch timing"
        )
        subtitle.setStyleSheet("font-size: 13px; color: #a0a0c0; padding-bottom: 8px;")
        layout.addWidget(subtitle)

        # ── Comparison table ────────────────────────
        self.table = QtWidgets.QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget {
                font-size: 14px;
                background-color: #1e1e34;
                gridline-color: #3a3a5a;
                border: 1px solid #3a3a5a;
            }
            QHeaderView::section {
                background-color: #2b2b48;
                color: #00d2ff;
                font-weight: bold;
                font-size: 14px;
                padding: 6px;
                border: 1px solid #3a3a5a;
            }
        """)
        layout.addWidget(self.table, stretch=2)

        # ── Formula used ────────────────────────────
        self.formula_label = QtWidgets.QLabel("")
        self.formula_label.setStyleSheet("font-size: 13px; color: #00ff88; padding: 6px; font-weight: bold;")
        layout.addWidget(self.formula_label)

        # ── Decay plot (from pivot 1) ───────────────
        bottom = QtWidgets.QHBoxLayout()
        self.decay_plot = pg.PlotWidget(title="Amplitude Decay Curve (Pivot 1)")
        self.decay_plot.setLabel('bottom', 'Swing Number (n)')
        self.decay_plot.setLabel('left', 'Amplitude θ (deg)')
        self.decay_plot.showGrid(x=True, y=True, alpha=0.3)
        bottom.addWidget(self.decay_plot, stretch=2)

        # ── Damping info ────────────────────────────
        damp_group = QtWidgets.QGroupBox("Damping Characteristics")
        damp_layout = QtWidgets.QFormLayout(damp_group)
        self.lbl_gamma = QtWidgets.QLabel("—")
        self.lbl_Q = QtWidgets.QLabel("—")
        self.lbl_delta = QtWidgets.QLabel("—")
        damp_layout.addRow("Decay constant (γ):", self.lbl_gamma)
        damp_layout.addRow("Quality factor (Q):", self.lbl_Q)
        damp_layout.addRow("Log decrement (δ):", self.lbl_delta)
        bottom.addWidget(damp_group, stretch=1)

        layout.addLayout(bottom, stretch=2)

        # ── Export buttons ──────────────────────────
        export_row = QtWidgets.QHBoxLayout()
        self.export_csv_btn = QtWidgets.QPushButton("💾 Export Raw CSV Data")
        self.export_csv_btn.setStyleSheet("padding: 10px; font-size: 14px; font-weight: bold;")
        self.export_json_btn = QtWidgets.QPushButton("📋 Export Session Summary JSON")
        self.export_json_btn.setStyleSheet("padding: 10px; font-size: 14px; font-weight: bold; background: #00d2ff; color: #111;")
        export_row.addWidget(self.export_csv_btn)
        export_row.addWidget(self.export_json_btn)
        layout.addLayout(export_row)

    def populate(self, experiment: Experiment):
        """Fill the dashboard with results from a completed experiment."""
        results = experiment.compute_results()
        t1 = experiment.trial1
        t2 = experiment.trial2

        # ── Build comparison table ──────────────────
        headers = ['Metric', 'Gyro (MPU6050)', 'IR Break-Beam', 'Manual Stopwatch']
        rows = [
            ['T1 (s)',
             f"{t1.T_gyro_mean:.5f} ± {t1.T_gyro_std:.5f}" if t1.T_gyro_mean else '—',
             f"{t1.T_ir_mean:.5f} ± {t1.T_ir_std:.5f}" if t1.T_ir_mean else '—',
             f"{t1.T_manual:.5f}" if t1.T_manual else '—'],
            ['T2 (s)',
             f"{t2.T_gyro_mean:.5f} ± {t2.T_gyro_std:.5f}" if t2.T_gyro_mean else '—',
             f"{t2.T_ir_mean:.5f} ± {t2.T_ir_std:.5f}" if t2.T_ir_mean else '—',
             f"{t2.T_manual:.5f}" if t2.T_manual else '—'],
            ['T1,0 (corrected s)',
             f"{t1.T_gyro_corrected:.5f}" if t1.T_gyro_corrected else '—',
             f"{t1.T_ir_corrected:.5f}" if t1.T_ir_corrected else '—',
             '— (no correction)'],
            ['T2,0 (corrected s)',
             f"{t2.T_gyro_corrected:.5f}" if t2.T_gyro_corrected else '—',
             f"{t2.T_ir_corrected:.5f}" if t2.T_ir_corrected else '—',
             '— (no correction)'],
            ['Calculated g (m/s²)',
             f"{results.get('g_gyro', 0):.5f}" if 'g_gyro' in results else '—',
             f"{results.get('g_ir', 0):.5f}" if 'g_ir' in results else '—',
             f"{results.get('g_manual', 0):.5f}" if 'g_manual' in results else '—'],
            ['Error vs Accepted Standard',
             f"{results.get('g_gyro_error_pct', 0):.4f} %" if 'g_gyro_error_pct' in results else '—',
             f"{results.get('g_ir_error_pct', 0):.4f} %" if 'g_ir_error_pct' in results else '—',
             f"{results.get('g_manual_error_pct', 0):.4f} %" if 'g_manual_error_pct' in results else '—'],
            ['Oscillations Counted',
             str(t1.n_oscillations_gyro + t2.n_oscillations_gyro),
             str(t1.n_oscillations_ir + t2.n_oscillations_ir),
             f"{(t1.n_oscillations_manual or 0) + (t2.n_oscillations_manual or 0)}"],
        ]

        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels(headers)
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                item = QtWidgets.QTableWidgetItem(val)
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(i, j, item)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch)

        # Formula used
        if 'g_gyro_formula' in results:
            self.formula_label.setText(
                f"Formula used: {results['g_gyro_formula']}  |  "
                f"Knife-edge distance L = {experiment.L} m  |  "
                f"Standard g = {experiment.g_accepted} m/s²"
            )

        # ── Decay plot ──────────────────────────────
        if t1.decay_swing_numbers:
            sn = np.array(t1.decay_swing_numbers)
            sa = np.array(t1.decay_amplitudes)
            self.decay_plot.clear()
            scatter = pg.ScatterPlotItem(sn, sa, pen=None, brush='#ff6b6b', size=6)
            self.decay_plot.addItem(scatter)

            if len(sn) > 3:
                theta0, gamma, Q = fit_decay(sn, sa)
                if gamma > 0:
                    fit_x = np.linspace(0, sn[-1], 200)
                    fit_y = theta0 * np.exp(-gamma * fit_x)
                    self.decay_plot.plot(fit_x, fit_y,
                                         pen=pg.mkPen('#00ff88', width=2,
                                                       style=QtCore.Qt.DashLine))
                    self.lbl_gamma.setText(f"{gamma:.6f}")
                    self.lbl_Q.setText(f"{Q:.1f}")
                    self.lbl_delta.setText(f"{gamma:.6f}")
