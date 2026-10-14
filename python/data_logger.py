"""Data logging: raw CSV export and JSON session summary."""

import csv
import json
import os
from datetime import datetime
from typing import List, Dict, Any


class DataLogger:
    """Logs raw IMU data to CSV and experiment results to JSON."""

    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self._csv_file = None
        self._csv_writer = None
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.saved_csvs: List[str] = []

    def start_csv(self, trial_name: str) -> str:
        """Open a CSV file for raw data logging."""
        path = os.path.join(self.output_dir,
                            f"{self._session_id}_{trial_name}.csv")
        self._csv_file = open(path, 'w', newline='')
        self._csv_writer = csv.writer(self._csv_file)
        self._csv_writer.writerow(
            ['t', 'ax', 'ay', 'az', 'gx', 'gy', 'gz', 'ir'])
        if path not in self.saved_csvs:
            self.saved_csvs.append(path)
        return path

    def write_sample(self, sample: dict):
        """Write one sample to the open CSV."""
        if self._csv_writer:
            self._csv_writer.writerow([
                f"{sample['t']:.4f}",
                f"{sample['ax']:.4f}", f"{sample['ay']:.4f}",
                f"{sample['az']:.4f}",
                f"{sample['gx']:.2f}", f"{sample['gy']:.2f}",
                f"{sample['gz']:.2f}",
                sample['ir']
            ])

    def stop_csv(self):
        """Close the CSV file."""
        if self._csv_file:
            self._csv_file.close()
            self._csv_file = None
            self._csv_writer = None

    def save_session(self, results: Dict[str, Any]) -> str:
        """Save complete session results to JSON."""
        path = os.path.join(self.output_dir,
                            f"{self._session_id}_results.json")
        results['session_id'] = self._session_id
        results['timestamp'] = datetime.now().isoformat()
        with open(path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        return path
