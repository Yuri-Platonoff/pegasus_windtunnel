from mfrc522 import MFRC522
import config


class RFIDReader:
    # Small wrapper around the MFRC522 driver.
    def __init__(self, sck, mosi, miso, rst, cs):
        self.reader = MFRC522(
            sck=sck,
            mosi=mosi,
            miso=miso,
            rst=rst,
            cs=cs
        )

        self.tag_speeds = config.TAG_SPEEDS

    def read_uid(self):
        # Read a tag and return its UID as a dash-separated string.
        status, _ = self.reader.request(self.reader.REQIDL)
        if status != self.reader.OK:
            return None

        status, raw_uid = self.reader.anticoll()
        if status != self.reader.OK:
            return None

        return "-".join(str(x) for x in raw_uid)

    def get_tag_info(self, uid):
        # Return the mapped name and speed for a UID.
        if uid in self.tag_speeds:
            speed_name, duty = self.tag_speeds[uid]
            return uid, speed_name, duty
        return uid, config.DEFAULT_SPEED_NAME, config.DEFAULT_SPEED_DUTY

    def read_tag_info(self):
        # Read a tag and return full mapped info in one step.
        uid = self.read_uid()
        if uid is None:
            return None
        return self.get_tag_info(uid)
