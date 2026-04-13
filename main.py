# main.py
# RFID + LCD + Button + Motor + Fan + Limit Switch

import utime
from machine import Pin, I2C

import config
from pico_i2c_lcd import I2cLcd
from rfid_reader import RFIDReader
from motor import MotorDriver
from button import Button


# ---------- LCD setup ----------
i2c = I2C(
    config.LCD_I2C_ID,
    sda=Pin(config.LCD_SDA_PIN),
    scl=Pin(config.LCD_SCL_PIN),
    freq=400000
)
lcd = I2cLcd(i2c, config.LCD_ADDR, config.LCD_ROWS, config.LCD_COLS)

# ---------- RFID setup ----------
rfid = RFIDReader(
    sck=config.RC522_SCK,
    mosi=config.RC522_MOSI,
    miso=config.RC522_MISO,
    rst=config.RC522_RST,
    cs=config.RC522_CS
)

# ---------- Motor setup ----------
motor = MotorDriver(
    pwm_pin=config.MOTOR_PWM_PIN,
    in1_pin=config.MOTOR_IN1_PIN,
    in2_pin=config.MOTOR_IN2_PIN,
    stby_pin=config.MOTOR_STBY_PIN,
    pwm_freq=config.PWM_FREQ
)

# ---------- Input devices ----------
button = Button(config.BUTTON_PIN)
limit_switch = Button(config.LIMIT_SWITCH_PIN)

# ---------- Fan setup ----------
fan = Pin(config.FAN_PIN, Pin.OUT)
fan.value(0)

# ---------- Tag map and timing ----------
TAG_SPEEDS = {
    "19-72-190-244-17": ("Thin + Round", 25000),
    "19-57-190-244-96": ("Thin + Pointy", 38000),
    "163-72-190-244-161": ("Thin + Flat", 50000),
    "35-123-191-244-19": ("Wide + Round", 38000),
    "211-121-191-244-225": ("Wide + Pointy", 53000),
    "115-118-191-244-78": ("Wide Flat", 65535),
}

RUN_TIME_MS = 6000
RAMP_UP_MS = 3000
RETURN_TIME_MS = 6000
RETURN_RAMP_MS = 3000

COUNTS_FILE = "counts.txt"

# Stores the last LCD message to avoid unnecessary rewrites.
last_lcd_line1 = None
last_lcd_line2 = None


# ---------- Count file helpers ----------
def load_counts():
    # Load saved counters from counts.txt.
    counts = {}

    try:
        with open(COUNTS_FILE, "r") as file:
            lines = file.readlines()

        for line in lines:
            line = line.strip()

            if not line:
                continue

            if ":" not in line:
                continue

            key, value = line.rsplit(":", 1)
            key = key.strip()
            value = value.strip()

            try:
                counts[key] = int(value)
            except ValueError:
                pass

        return counts

    except OSError:
        return {}


def save_counts(counts):
    # Save the current counters in a readable format.
    with open(COUNTS_FILE, "w") as file:
        file.write("=== SYSTEM COUNTS ===\n")
        file.write("Button Presses: " +
                   str(counts.get("button_presses", 0)) + "\n")
        file.write("RFID Reads: " +
                   str(counts.get("rfid_reads", 0)) + "\n")
        file.write("Limit Switch Passed: " +
                   str(counts.get("limit_switch_ok", 0)) + "\n")

        file.write("\n=== ROCKET TEST COUNTS ===\n")

        rocket_names = []
        for name, _duty in config.TAG_SPEEDS.values():
            if name not in rocket_names:
                rocket_names.append(name)

        for name in rocket_names:
            file.write(name + ": " + str(counts.get(name, 0)) + "\n")

    print("counts.txt saved:", counts)


def increment_count(counts, key):
    # Increase one counter and save immediately.
    if key not in counts:
        counts[key] = 0
    counts[key] += 1
    save_counts(counts)


# ---------- LCD helpers ----------
def lcd_show(line1="", line2="", force=False):
    # Show up to 16 characters per line on the LCD.
    global last_lcd_line1, last_lcd_line2

    line1 = str(line1)[:16]
    line2 = str(line2)[:16]

    if (not force) and line1 == last_lcd_line1 and line2 == last_lcd_line2:
        return

    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(line1)
    lcd.move_to(0, 1)
    lcd.putstr(line2)

    last_lcd_line1 = line1
    last_lcd_line2 = line2


# ---------- RFID helpers ----------
def wait_for_new_tag():
    # Wait until a new RFID tag is scanned.
    last_uid = None

    while True:
        uid = rfid.read_uid()

        if uid is not None:
            if uid != last_uid:
                return uid
            last_uid = uid
        else:
            last_uid = None

        utime.sleep_ms(100)


def wait_for_tag_removed(scanned_uid):
    # Wait until the scanned tag is removed from the reader.
    while True:
        uid = rfid.read_uid()
        if uid is None or uid != scanned_uid:
            break
        utime.sleep_ms(100)


# ---------- User input / safety helpers ----------
def wait_for_start_button(counts):
    # Wait for the user to press the start button.
    print("Waiting for start button...")
    lcd_show("Press button", "to start")
    button.wait_for_press()
    increment_count(counts, "button_presses")
    lcd_show("Starting...", "")
    utime.sleep_ms(800)


def wait_for_limit_switch(counts=None):
    # Make sure the tube is closed before starting the launch.
    print("Checking limit switch...")

    if not limit_switch.is_pressed():
        lcd_show("Close tube", "Press switch", force=True)

    while not limit_switch.is_pressed():
        motor.stop()
        fan.value(0)
        utime.sleep_ms(100)

    print("Limit switch pressed.")
    if counts is not None:
        increment_count(counts, "limit_switch_ok")
    lcd_show("Tube closed", "Starting soon", force=True)
    utime.sleep_ms(500)


# ---------- Startup checks ----------
def startup_diagnostics():
    # Basic startup check so failures are easier to spot.
    global lcd, rfid, motor, button, fan, limit_switch

    print("=== STARTUP DIAGNOSTICS ===")

    errors = []
    passes = []

    try:
        passes.append("LCD")
        print("[PASS] LCD initialized")
    except Exception as err:
        errors.append("LCD init failed")
        print("[FAIL] LCD init failed:", err)

    try:
        passes.append("RFID")
        print("[PASS] RFID initialized")
    except Exception as err:
        errors.append("RFID init failed")
        print("[FAIL] RFID init failed:", err)

    try:
        passes.append("Motor")
        print("[PASS] Motor initialized")
    except Exception as err:
        errors.append("Motor init failed")
        print("[FAIL] Motor init failed:", err)

    try:
        passes.append("Button")
        print("[PASS] Button initialized")
    except Exception as err:
        errors.append("Button init failed")
        print("[FAIL] Button init failed:", err)

    try:
        passes.append("Limit switch")
        print("[PASS] Limit switch initialized")
    except Exception as err:
        errors.append("Limit switch init failed")
        print("[FAIL] Limit switch init failed:", err)

    try:
        passes.append("Fan")
        print("[PASS] Fan initialized")
    except Exception as err:
        errors.append("Fan init failed")
        print("[FAIL] Fan init failed:", err)

    print("=== DIAGNOSTICS COMPLETE ===")
    print("Passes:", len(passes))
    print("Errors:", len(errors))

    return errors


# ---------- Main program ----------
def main():
    errors = startup_diagnostics()

    if errors:
        print("\nStartup errors found:")
        for err in errors:
            print("-", err)
        print("\nFix the problem(s) above and run again.")
        return

    print("System ready.")
    counts = load_counts()

    # Wait on power-up for initial start button.
    wait_for_start_button(counts)

    while True:
        wait_for_start_button(counts)
        lcd_show("Build and place", "rocket")

        uid = wait_for_new_tag()
        print("RFID Tag Scanned:", uid)

        if uid in TAG_SPEEDS:
            speed_name, duty = TAG_SPEEDS[uid]
            print("Matched speed:", speed_name, duty)

            increment_count(counts, speed_name)
            increment_count(counts, "rfid_reads")

            lcd_show("You placed:", speed_name)
            utime.sleep_ms(2000)

            lcd_show("Press button", "to start")
            print("Waiting for button press...")
            button.wait_for_press()
            increment_count(counts, "button_presses")

            # Only check the limit switch here, right before launch.
            wait_for_limit_switch(counts)

            lcd_show("Testing...", speed_name)
            print("Running motor forward and fan...")

            fan.value(1)

            # Forward run
            motor.run_profile(
                duty,
                total_time_ms=RUN_TIME_MS,
                ramp_up_ms=RAMP_UP_MS,
                reverse=False
            )

            utime.sleep_ms(4000)

            lcd_show("Returning to", "Earth")
            print("Returning to start...")

            fan.value(1)

            # Return run
            motor.run_profile(
                duty,
                total_time_ms=RETURN_TIME_MS,
                ramp_up_ms=RETURN_RAMP_MS,
                reverse=True
            )

            fan.value(0)

            # Final result message
            if speed_name == "Thin + Round":
                lcd_show("Best solution!", "Good Job!", force=True)
                print("Best solution found, remove your rocket")
                utime.sleep_ms(2000)
                lcd_show("Remove rocket", "", force=True)
            else:
                lcd_show("Try again with", "different parts", force=True)
                print("Try again with different parts")

            utime.sleep_ms(3000)

        else:
            print("Unknown tag")
            lcd_show("Unknown item", "Try again")
            utime.sleep_ms(1500)

        wait_for_tag_removed(uid)


main()
