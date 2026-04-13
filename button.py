from machine import Pin
import utime


class Button:
    # Simple active-low button/limit-switch wrapper.
    def __init__(self, pin_num: int):
        self.pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)

    def is_pressed(self):
        # Returns True when the button or switch is pressed.
        return self.pin.value() == 0

    def wait_for_press(self):
        # Wait for a full press-and-release with simple debounce.
        while self.pin.value() == 1:
            utime.sleep_ms(10)

        utime.sleep_ms(30)

        while self.pin.value() == 0:
            utime.sleep_ms(10)

        utime.sleep_ms(30)
