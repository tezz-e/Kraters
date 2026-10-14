"""2D pendulum visualization: rod + bob + velocity arrow + trail."""

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore

ROD_LEN = 0.8
TRAIL_LEN = 200


class PendulumWidget(pg.PlotWidget):
    """Animated pendulum arm with velocity arrow and motion trail."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAspectLocked(True)
        self.setXRange(-1.2, 1.2)
        self.setYRange(-1.4, 0.3)
        self.setTitle("Live Pendulum Motion")
        self.hideAxis('bottom')
        self.hideAxis('left')
        self.setBackground('#1a1a2e')

        # Pivot point
        self.plot([0], [0], pen=None, symbol='o', symbolSize=12, symbolBrush='w')

        # Rod + bob + arrow
        self.rod = self.plot([0, 0], [0, -ROD_LEN],
                             pen=pg.mkPen('#e0e0e0', width=3))
        self.bob = self.plot([0], [-ROD_LEN], pen=None, symbol='o',
                             symbolSize=18, symbolBrush='#ff6b6b')
        self.arrow_line = self.plot([0, 0], [-ROD_LEN, -ROD_LEN],
                                    pen=pg.mkPen('#00d2ff', width=3))
        self.arrowhead = self.plot([0], [-ROD_LEN], pen=None, symbol='t',
                                   symbolSize=14, symbolBrush='#00d2ff')

        # Motion trail
        self.trail_x, self.trail_y = [], []
        self.trail_curve = self.plot([], [], pen=pg.mkPen('#ff6b6b44', width=1))

        # Angle label
        self.angle_text = pg.TextItem("theta = 0.0 deg", color='w', anchor=(0, 0))
        self.angle_text.setPos(-1.1, 0.2)
        self.addItem(self.angle_text)

    def update_pendulum(self, theta_rad: float, gyro_rate: float):
        bx = ROD_LEN * np.sin(theta_rad)
        by = -ROD_LEN * np.cos(theta_rad)

        # Velocity arrow (tangential to circular path)
        if abs(gyro_rate) > 1.0:
            scale = 0.12 + min(abs(gyro_rate) / 80.0, 0.35)
            tx, ty = np.cos(theta_rad), np.sin(theta_rad)
            sign = 1.0 if gyro_rate >= 0 else -1.0
            ax_e = bx + sign * tx * scale
            ay_e = by + sign * ty * scale
            self.arrow_line.setData([bx, ax_e], [by, ay_e])
            self.arrowhead.setData([ax_e], [ay_e])
        else:
            self.arrow_line.setData([], [])
            self.arrowhead.setData([], [])

        # Trail history
        self.trail_x.append(bx)
        self.trail_y.append(by)
        if len(self.trail_x) > TRAIL_LEN:
            self.trail_x = self.trail_x[-TRAIL_LEN:]
            self.trail_y = self.trail_y[-TRAIL_LEN:]
        self.trail_curve.setData(self.trail_x, self.trail_y)

        self.angle_text.setText(f"theta = {np.degrees(theta_rad):.1f} deg")

    def reset_trail(self):
        self.trail_x.clear()
        self.trail_y.clear()
        self.trail_curve.setData([], [])
