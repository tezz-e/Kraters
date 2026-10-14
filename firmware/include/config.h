#pragma once

// ── I2C (MPU6050) for ESP8266 NodeMCU ────────────
#define I2C_SDA D2   // GPIO 4
#define I2C_SCL D1   // GPIO 5

// ── IR Break-Beam Sensor ─────────────────────────
#define IR_SENSOR_PIN D5   // GPIO 14 (Digital input, INPUT_PULLUP)

// ── Streaming ────────────────────────────────────
#define STREAM_INTERVAL_MS 10   // 100 Hz
#define SERIAL_BAUD 115200

// ── MPU6050 Axis Mapping ─────────────────────────
// Sensor mounted flat on the rod:
//   Z-axis -> along the rod (toward pivot)
//   X-axis -> tangential to swing plane
// Swing-plane gyro: X-axis
