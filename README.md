# Pegasus P2 – Interactive Rocket Exhibit

## Overview
This project is a portable, interactive museum exhibit designed for children (ages ~8–12) to learn about aerodynamics and rocket design through hands-on interaction.

Users:
1. Build a rocket (nose cone type)
2. Scan it using RFID
3. Run a wind tunnel test (motor + fan system)
4. Observe results and try to optimize their design

The system is powered by a Raspberry Pi Pico (MicroPython) and integrates multiple hardware components.

---

## Features

- RFID-based rocket identification
- LCD instructions and feedback
- Button-controlled interaction flow
- Limit switch safety system (prevents running when open)
- Motor with realistic acceleration/deceleration profiles
- Fan activation during testing
- Persistent data logging (`counts.txt`)
- Interactive result feedback:
  - Best design: "Thin + Round"
  - Others: "Try again with different parts"

---

## How It Works

### User Flow
1. Press button to start
2. Place rocket (RFID tag)
3. Scan rocket
4. Press button to confirm
5. System checks limit switch (tube closed)
6. Motor + fan run forward (test)
7. System returns to start
8. Result displayed on LCD

---

## Hardware Components

- Raspberry Pi Pico
- MFRC522 RFID Reader
- I2C LCD Display (16x2)
- TB6612FNG Motor Driver
- DC Motor (track system)
- Fan (transistor-controlled)
- Push Button (start)
- Limit Switch (safety)

---

## Pin Configuration

Defined in `config.py`:

| Component       | Pin  |
|----------------|------|
| Button         | GP16 |
| Limit Switch   | GP15 |
| Fan            | GP14 |
| Motor PWM      | GP10 |
| Motor IN1      | GP11 |
| Motor IN2      | GP12 |
| Motor STBY     | GP13 |
| LCD SDA        | GP26 |
| LCD SCL        | GP27 |
| RFID (SPI)     | GP0–GP4 |

---

## 🗂️ File Structure
main.py # Main system logic (control flow)
config.py # Pin assignments + RFID mappings
motor.py # Motor driver + speed profiles
button.py # Button handling
rfid_reader.py # RFID abstraction layer
mfrc522.py # Low-level RFID driver
lcd_api.py # LCD base driver
pico_i2c_lcd.py # LCD I2C interface
counts.txt # Runtime statistics (auto-generated)


---

## Key Behaviors

### Safety System
- System will NOT run unless the limit switch is pressed
- Prevents running when the tube is open

### Motor Profile
Motor uses a curved speed profile:
- Ramp up → peak → ramp down
- More realistic motion for demonstration

### RFID Mapping
Defined in `config.py`:

Example:
```python
"19-72-190-244-17": ("Thin + Round", 25000)
