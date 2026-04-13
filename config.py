# config.py
# Central place for pin assignments and project settings.

# ---------- RFID RC522 ----------
RC522_SCK = 2
RC522_MOSI = 3
RC522_MISO = 4
RC522_RST = 0
RC522_CS = 1

# ---------- Button ----------
BUTTON_PIN = 16

# ---------- LCD I2C ----------
LCD_I2C_ID = 1
LCD_SDA_PIN = 26
LCD_SCL_PIN = 27
LCD_ADDR = 0x27        # Try 0x3F if 0x27 does not work
LCD_ROWS = 2
LCD_COLS = 16

# ---------- Motor driver TB6612FNG ----------
MOTOR_PWM_PIN = 10     # PWMA
MOTOR_IN1_PIN = 11     # AIN1
MOTOR_IN2_PIN = 12     # AIN2
MOTOR_STBY_PIN = 13    # STBY

PWM_FREQ = 1000
MOTOR_RUN_TIME_MS = 3000

# ---------- Fan control ----------
FAN_PIN = 14

# ---------- Limit switch ----------
LIMIT_SWITCH_PIN = 15

# ---------- RFID -> speed map ----------
# Each tag maps to a rocket name and motor duty value.
TAG_SPEEDS = {
    "19-72-190-244-17": ("Thin + Round", 25000),
    "19-57-190-244-96": ("Thin + Pointy", 38000),
    "163-72-190-244-161": ("Thin + Flat", 50000),
    "35-123-191-244-19": ("Wide + Round", 38000),
    "211-121-191-244-225": ("Wide + Pointy", 53000),
    "115-118-191-244-78": ("Wide Flat", 65535),
}

DEFAULT_TAG_NAME = "Unknown Tag"
DEFAULT_SPEED_NAME = "Low Speed"
DEFAULT_SPEED_DUTY = 25000
