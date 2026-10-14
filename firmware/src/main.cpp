#include <Arduino.h>
#include <Wire.h>
#include <MPU6050_light.h>
#include "config.h"

MPU6050 mpu(Wire);
unsigned long lastStreamTimeUs = 0;
bool streaming = false;

// ── IR Interrupt-driven state ─────────────
volatile int ir_idle_val = HIGH;
volatile unsigned long t_enter_us = 0;
volatile unsigned long t_exit_us = 0;
volatile unsigned long last_ir_mid_us = 0;
volatile bool ir_mid_ready = false;
volatile bool ir_latched = false;
volatile unsigned long last_edge_time_us = 0;

IRAM_ATTR void irISR() {
    unsigned long now_us = micros();
    if (now_us - last_edge_time_us < 2000) return; // 2 ms debounce
    last_edge_time_us = now_us;

    int pinVal = digitalRead(IR_SENSOR_PIN);
    if (pinVal != ir_idle_val) {
        // Beam broken (entry)
        t_enter_us = now_us;
        ir_latched = true;
    } else if (t_enter_us != 0) {
        // Beam restored (exit) -> compute exact center midpoint
        t_exit_us = now_us;
        last_ir_mid_us = (t_enter_us + t_exit_us) / 2;
        ir_mid_ready = true;
        t_enter_us = 0;
    }
}

void runCalibration() {
    Serial.println("# CALIBRATING");
    delay(500);
    // Gyroscope-only calibration: do NOT calibrate accelerometer offsets
    // because that assumes +1g on Z and corrupts orientation on Pivot 2
    mpu.calcOffsets(true, false);
    ir_idle_val = digitalRead(IR_SENSOR_PIN);
    Serial.println("# CAL_DONE");
}

void handleCommand(const String& cmd) {
    if (cmd == "CMD:CAL") {
        runCalibration();
    } else if (cmd == "CMD:PING") {
        Serial.println("# PONG");
    }
}

void setup() {
    Serial.begin(SERIAL_BAUD);
    delay(1000);
    
    // IR sensor pin + interrupt
    pinMode(IR_SENSOR_PIN, INPUT_PULLUP);
    ir_idle_val = digitalRead(IR_SENSOR_PIN);
    attachInterrupt(digitalPinToInterrupt(IR_SENSOR_PIN), irISR, CHANGE);

    // I2C + MPU6050
    Wire.begin(I2C_SDA, I2C_SCL);
    Wire.setClock(400000);

    byte status = mpu.begin();
    Serial.print("# MPU6050 status: ");
    Serial.println(status);
    if (status != 0) {
        Serial.println("# ERROR: MPU6050 not found!");
        while (1) {
            delay(1000);
        }
    }

    // Initial gyro-only calibration
    Serial.println("# Initial calibration... keep pendulum still");
    runCalibration();

    // Column header
    Serial.println("# columns: timestamp_ms,ax,ay,az,gx,gy,gz,ir");
    Serial.println("# units: ms, g, g, g, deg/s, deg/s, deg/s, 0/1");
    Serial.println("# STREAM_START");
    streaming = true;
}

void loop() {
    // Check for incoming commands from Python
    if (Serial.available()) {
        String line = Serial.readStringUntil('\n');
        line.trim();
        if (line.startsWith("CMD:")) {
            handleCommand(line);
        }
    }

    // Flush any interrupt-detected IR center midpoint immediately
    if (ir_mid_ready) {
        ir_mid_ready = false;
        Serial.printf("# IR_MID:%.6f\n", last_ir_mid_us / 1000000.0);
    }

    mpu.update();

    if (!streaming) return;

    unsigned long now_us = micros();
    if (now_us - lastStreamTimeUs >= (STREAM_INTERVAL_MS * 1000UL)) {
        lastStreamTimeUs = now_us;
        
        // 8th column is 1 if currently broken or latched broken since last tick
        bool is_broken = (digitalRead(IR_SENSOR_PIN) != ir_idle_val) || ir_latched;
        ir_latched = false;

        // CSV: timestamp_ms (%.3f), ax, ay, az, gx, gy, gz, ir (0 or 1)
        Serial.printf("%.3f,%.4f,%.4f,%.4f,%.2f,%.2f,%.2f,%d\n",
                      now_us / 1000.0,
                      mpu.getAccX(), mpu.getAccY(), mpu.getAccZ(),
                      mpu.getGyroX(), mpu.getGyroY(), mpu.getGyroZ(),
                      is_broken ? 1 : 0);
    }
}
