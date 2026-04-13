from machine import Pin, PWM
import utime


class MotorDriver:
    # Simple TB6612FNG motor driver wrapper.
    def __init__(self, pwm_pin, in1_pin, in2_pin, stby_pin, pwm_freq=1000):
        self.in1 = Pin(in1_pin, Pin.OUT)
        self.in2 = Pin(in2_pin, Pin.OUT)
        self.stby = Pin(stby_pin, Pin.OUT)

        self.pwm = PWM(Pin(pwm_pin))
        self.pwm.freq(pwm_freq)
        self.pwm.duty_u16(0)

        self.stop()

    def enable(self):
        # Wake the driver from standby.
        self.stby.value(1)

    def disable(self):
        # Put the driver into standby.
        self.stby.value(0)

    def forward(self, duty):
        # Run the motor forward at the requested PWM duty.
        self.enable()
        self.in1.value(1)
        self.in2.value(0)
        self.pwm.duty_u16(max(0, min(65535, int(duty))))

    def reverse(self, duty):
        # Run the motor in reverse at the requested PWM duty.
        self.enable()
        self.in1.value(0)
        self.in2.value(1)
        self.pwm.duty_u16(max(0, min(65535, int(duty))))

    def stop(self):
        # Stop the motor and disable the driver.
        self.pwm.duty_u16(0)
        self.in1.value(0)
        self.in2.value(0)
        self.disable()

    def run_for(self, duty, run_time_ms, reverse=False):
        # Run at one fixed speed for a set amount of time.
        if reverse:
            self.reverse(duty)
        else:
            self.forward(duty)

        utime.sleep_ms(run_time_ms)
        self.stop()

    def run_profile(self, peak_duty, total_time_ms=1000,
                    ramp_up_ms=300, step_ms=20, reverse=False):
        # Run a curved speed profile: ramp up, then ramp down.

        peak_duty = max(0, min(65535, int(peak_duty)))
        total_time_ms = int(total_time_ms)
        ramp_up_ms = int(ramp_up_ms)
        step_ms = int(step_ms)

        if total_time_ms <= 0:
            self.stop()
            return

        if ramp_up_ms <= 0:
            ramp_up_ms = 1

        if ramp_up_ms >= total_time_ms:
            ramp_up_ms = total_time_ms // 2

        ramp_down_ms = total_time_ms - ramp_up_ms

        ramp_up_steps = max(1, ramp_up_ms // step_ms)
        ramp_down_steps = max(1, ramp_down_ms // step_ms)

        self.enable()

        if reverse:
            self.in1.value(0)
            self.in2.value(1)
        else:
            self.in1.value(1)
            self.in2.value(0)

        # Ramp up with a simple curve.
        for i in range(1, ramp_up_steps + 1):
            x = i / ramp_up_steps
            curve = x * x
            duty = int(peak_duty * curve)
            self.pwm.duty_u16(duty)
            utime.sleep_ms(step_ms)

        # Ramp back down to zero.
        for i in range(1, ramp_down_steps + 1):
            x = i / ramp_down_steps
            curve = (1 - x) * (1 - x)
            duty = int(peak_duty * curve)
            self.pwm.duty_u16(duty)
            utime.sleep_ms(step_ms)

        self.stop()
