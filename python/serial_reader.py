"""Threaded serial reader for ESP32/ESP8266 CSV data (MPU6050 + IR sensor)."""

import threading
import queue
import serial
import numpy as np


class SerialReader(threading.Thread):
    """Reads 8-column CSV from ESP, pushes parsed dicts to a queue.
    
    CSV: timestamp_ms, ax, ay, az, gx, gy, gz, ir
    Lines starting with '#' are metadata.
    """

    def __init__(self, port: str, baud: int = 115200):
        super().__init__(daemon=True)
        self.port = port
        self.baud = baud
        self.data_queue = queue.Queue(maxsize=10000)
        self.meta_queue = queue.Queue(maxsize=100)  # metadata/status messages
        self.running = True
        self.connected = False
        self.stream_started = False
        self._ser = None

        # Rest-state accelerometer (self-calibrating g reference)
        self.a_rest = None
        self.a_perp_rest = 0.0
        self.a_y_rest = 0.0
        self.dominant_axis = 'az'
        self.suggested_gyro = 'gy'
        self._rest_samples = []
        self._collecting_rest = False

    def connect(self) -> bool:
        """Attempt to open the serial port. Returns True on success."""
        try:
            self._ser = serial.Serial(self.port, self.baud, timeout=1)
            self.connected = True
            return True
        except Exception as e:
            self.meta_queue.put(f"ERROR: {e}")
            return False

    def send_command(self, cmd: str):
        """Send a command string to the ESP (e.g., 'CMD:CAL')."""
        if self._ser and self._ser.is_open:
            self._ser.write(f"{cmd}\n".encode())

    def start_rest_calibration(self):
        """Begin collecting rest samples for a_rest measurement."""
        self._rest_samples = []
        self._collecting_rest = True
        self.a_rest = None
        self.a_perp_rest = 0.0
        self.a_y_rest = 0.0

    def run(self):
        if not self._ser:
            if not self.connect():
                return

        while self.running:
            try:
                raw = self._ser.readline()
                if not raw:
                    continue
                line = raw.decode('utf-8', errors='ignore').strip()
                if not line:
                    continue

                # Metadata lines
                if line.startswith('#'):
                    if line.startswith('# IR_MID:'):
                        try:
                            t_sec = float(line.split(':')[1])
                            self.meta_queue.put(('IR_MID', t_sec))
                        except Exception:
                            pass
                    elif 'CAL_DONE' in line:
                        self.meta_queue.put('CAL_DONE')
                        self.start_rest_calibration()
                    else:
                        self.meta_queue.put(line)

                    if 'STREAM_START' in line:
                        self.stream_started = True
                    continue

                # Parse CSV: timestamp, ax, ay, az, gx, gy, gz, ir
                parts = line.split(',')
                if len(parts) != 8:
                    continue

                vals = [float(x) for x in parts]
                sample = {
                    't': vals[0] / 1000.0,   # seconds
                    'ax': vals[1], 'ay': vals[2], 'az': vals[3],
                    'gx': vals[4], 'gy': vals[5], 'gz': vals[6],
                    'ir': int(vals[7]),
                }

                # Collect rest-state samples for g reference
                if self._collecting_rest:
                    self._rest_samples.append((sample['az'], sample['ax'], sample['ay']))
                    if len(self._rest_samples) >= 100:
                        arr = np.array(self._rest_samples)
                        mean_z = float(np.mean(arr[:, 0]))
                        mean_x = float(np.mean(arr[:, 1]))
                        mean_y = float(np.mean(arr[:, 2]))
                        abs_axes = {'az': abs(mean_z), 'ay': abs(mean_y), 'ax': abs(mean_x)}
                        dominant = max(abs_axes, key=abs_axes.get)
                        if dominant == 'ay':
                            self.a_rest = mean_y
                            self.a_perp_rest = mean_x
                            self.dominant_axis = 'ay'
                            self.suggested_gyro = 'gz'
                        elif dominant == 'ax':
                            self.a_rest = mean_x
                            self.a_perp_rest = mean_y
                            self.dominant_axis = 'ax'
                            self.suggested_gyro = 'gz'
                        else:  # az
                            self.a_rest = mean_z
                            self.a_perp_rest = mean_x
                            self.dominant_axis = 'az'
                            self.suggested_gyro = 'gy'

                        self._collecting_rest = False
                        self.meta_queue.put(
                            f"REST_CAL: dominant={self.dominant_axis}, a_rest={self.a_rest:.4f}g, a_perp={self.a_perp_rest:.4f}g"
                        )
                        self.meta_queue.put("REST_CAL_DONE")

                self.data_queue.put(sample)

            except (ValueError, serial.SerialException):
                continue
            except Exception as e:
                self.meta_queue.put(f"ERROR: {e}")
                continue

        if self._ser:
            self._ser.close()

    def stop(self):
        self.running = False
