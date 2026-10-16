"""Setup page: COM port, parameters, connection test."""

from PyQt5 import QtWidgets, QtCore
import serial.tools.list_ports


class SetupPage(QtWidgets.QWidget):
    """Step 1: Connect to ESP and enter experiment parameters.
    
    Signals:
        connected(str, int)  - emitted with (port, baud) on successful connect
        proceed()            - emitted when user clicks Next
    """
    connected = QtCore.pyqtSignal(str, int)
    proceed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        # Title
        title = QtWidgets.QLabel("Step 1 - Setup & Hardware Connection")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #00d2ff; padding-bottom: 10px;")
        layout.addWidget(title)

        # ── Connection group ────────────────────────
        conn_group = QtWidgets.QGroupBox("Microcontroller Connection")
        conn_layout = QtWidgets.QHBoxLayout(conn_group)

        self.port_combo = QtWidgets.QComboBox()
        self.port_combo.setMinimumWidth(250)
        self.refresh_ports()
        conn_layout.addWidget(QtWidgets.QLabel("COM Port:"))
        conn_layout.addWidget(self.port_combo)

        refresh_btn = QtWidgets.QPushButton("Refresh Ports")
        refresh_btn.clicked.connect(self.refresh_ports)
        conn_layout.addWidget(refresh_btn)

        self.connect_btn = QtWidgets.QPushButton("Connect")
        self.connect_btn.setStyleSheet("font-weight: bold; padding: 6px 16px;")
        conn_layout.addWidget(self.connect_btn)

        self.status_label = QtWidgets.QLabel("● Not connected")
        self.status_label.setStyleSheet("color: #ff4444; font-weight: bold; padding-left: 10px;")
        conn_layout.addWidget(self.status_label)

        layout.addWidget(conn_group)

        # ── Live sensor preview label ───────────────
        self.preview_label = QtWidgets.QLabel("Live sensor data will appear here once connected...")
        self.preview_label.setStyleSheet("color: #00d2ff; font-family: Consolas, monospace; font-size: 13px; padding: 8px; background: #18182c; border-radius: 4px;")
        layout.addWidget(self.preview_label)

        # ── Parameters group ────────────────────────
        params_group = QtWidgets.QGroupBox("Experiment Geometry & Parameters")
        params_layout = QtWidgets.QFormLayout(params_group)

        self.L_input = QtWidgets.QDoubleSpinBox()
        self.L_input.setRange(0.01, 5.0)
        self.L_input.setDecimals(4)
        self.L_input.setValue(1.0)
        self.L_input.setSuffix(" m")
        self.L_input.valueChanged.connect(self._sync_h_from_inputs)
        params_layout.addRow("Knife-edge distance (L):", self.L_input)

        self.h1_input = QtWidgets.QDoubleSpinBox()
        self.h1_input.setRange(0.0, 5.0)
        self.h1_input.setDecimals(4)
        self.h1_input.setValue(0.4300)
        self.h1_input.setSuffix(" m")
        self.h1_input.valueChanged.connect(self._sync_h_from_inputs)
        params_layout.addRow("h1 (Pivot 1 Knife Edge to Center of Mass):", self.h1_input)

        self.h2_input = QtWidgets.QDoubleSpinBox()
        self.h2_input.setRange(0.0, 5.0)
        self.h2_input.setDecimals(4)
        self.h2_input.setValue(0.5700)
        self.h2_input.setSuffix(" m")
        self.h2_input.valueChanged.connect(self._sync_h_from_inputs)
        params_layout.addRow("h2 (Pivot 2 Knife Edge to Center of Mass):", self.h2_input)

        self.h_input = QtWidgets.QDoubleSpinBox()
        self.h_input.setRange(-2.0, 2.0)
        self.h_input.setDecimals(4)
        self.h_input.setValue(-0.1400)
        self.h_input.setSuffix(" m")
        self.h_input.setSpecialValueText("0.0 (use ideal formula)")
        self.h_input.valueChanged.connect(self._on_h_diff_changed)
        params_layout.addRow("h1 - h2 (Bessel's asymmetry):", self.h_input)

        self.lbl_h_check = QtWidgets.QLabel("✅ h1 + h2 = 1.0000 m (matches L). Bessel asymmetry = -0.1400 m")
        self.lbl_h_check.setStyleSheet("color: #00ff88; font-size: 12px; font-weight: bold; padding: 2px;")
        params_layout.addRow("", self.lbl_h_check)

        self.g_input = QtWidgets.QDoubleSpinBox()
        self.g_input.setRange(9.0, 10.0)
        self.g_input.setDecimals(5)
        self.g_input.setValue(9.80665)
        self.g_input.setSuffix(" m/s²")
        params_layout.addRow("Accepted g (reference standard):", self.g_input)

        layout.addWidget(params_group)

        # ── Instructions ────────────────────────────
        info = QtWidgets.QLabel(
            "Quick Instructions:\n"
            "1. Connect the ESP via USB (CH340 driver on COM port)\n"
            "2. Mount MPU6050 flat on pendulum rod (Z-axis along rod toward pivot)\n"
            "3. Verify Knife-Edge distance L (1.000 m) & balance point (h1 ≈ 0.43m, h2 ≈ 0.57m)\n"
            "4. Click 'Connect' to initialize the serial data stream\n"
            "5. Click 'Next' to begin the Pivot 1 trial"
        )
        info.setStyleSheet("color: #b0b0b0; font-size: 13px; line-height: 1.5; padding: 12px; background: #22223a; border-radius: 6px;")
        layout.addWidget(info)

        # ── Next button ─────────────────────────────
        self.next_btn = QtWidgets.QPushButton("Next -> Begin Pivot 1 Trial")
        self.next_btn.setEnabled(False)
        self.next_btn.setStyleSheet(
            "font-size: 16px; font-weight: bold; padding: 14px; background: #00d2ff; color: #111; border-radius: 6px;")
        self.next_btn.clicked.connect(self.proceed.emit)
        layout.addWidget(self.next_btn)

        layout.addStretch()

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        default_idx = 0
        for i, p in enumerate(ports):
            self.port_combo.addItem(f"{p.device} - {p.description}", p.device)
            if "COM13" in p.device:
                default_idx = i
        if ports:
            self.port_combo.setCurrentIndex(default_idx)

    def set_connected(self, success: bool):
        if success:
            self.status_label.setText("● Connected")
            self.status_label.setStyleSheet("color: #00ff88; font-weight: bold; padding-left: 10px;")
            self.next_btn.setEnabled(True)
        else:
            self.status_label.setText("● Connection failed")
            self.status_label.setStyleSheet("color: #ff4444; font-weight: bold; padding-left: 10px;")

    def update_preview(self, sample: dict):
        ir_text = "Beam CLEAR" if sample.get('ir', 1) == 1 else "BEAM BROKEN"
        self.preview_label.setText(
            f"LIVE: ax={sample['ax']:+.3f}g  ay={sample['ay']:+.3f}g  az={sample['az']:+.3f}g  |  "
            f"gx={sample['gx']:+.1f}°/s  gy={sample['gy']:+.1f}°/s  |  IR: {ir_text}"
        )

    def _sync_h_from_inputs(self):
        h1 = self.h1_input.value()
        h2 = self.h2_input.value()
        L = self.L_input.value()
        h_diff = h1 - h2
        self.h_input.blockSignals(True)
        self.h_input.setValue(h_diff)
        self.h_input.blockSignals(False)

        h_sum = h1 + h2
        if abs(h_sum - L) <= 0.01:
            self.lbl_h_check.setText(f"✅ h1 + h2 = {h_sum:.4f} m (matches L = {L:.4f} m). Bessel asymmetry = {h_diff:+.4f} m")
            self.lbl_h_check.setStyleSheet("color: #00ff88; font-size: 12px; font-weight: bold; padding: 2px;")
        else:
            self.lbl_h_check.setText(f"⚠️ Note: h1 + h2 ({h_sum:.3f} m) != L ({L:.3f} m). Measure from knife-edge blade apex, not rod ends!")
            self.lbl_h_check.setStyleSheet("color: #ffaa00; font-size: 12px; font-weight: bold; padding: 2px;")

    def _on_h_diff_changed(self):
        h_diff = self.h_input.value()
        if abs(h_diff) < 1e-5:
            self.lbl_h_check.setText("ℹ️ h1 - h2 is 0.0; ideal equal-period formula will be used.")
            self.lbl_h_check.setStyleSheet("color: #00d2ff; font-size: 12px; font-weight: bold; padding: 2px;")
        else:
            self.lbl_h_check.setText(f"ℹ️ Custom Bessel asymmetry h1 - h2 = {h_diff:+.4f} m")
            self.lbl_h_check.setStyleSheet("color: #00d2ff; font-size: 12px; font-weight: bold; padding: 2px;")

    def get_port(self) -> str:
        return self.port_combo.currentData() or self.port_combo.currentText().split()[0]

    def get_params(self) -> dict:
        h = self.h_input.value()
        return {
            'L': self.L_input.value(),
            'h1': self.h1_input.value(),
            'h2': self.h2_input.value(),
            'h1_minus_h2': h if abs(h) > 1e-5 else None,
            'g_accepted': self.g_input.value(),
        }
