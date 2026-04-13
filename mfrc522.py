from machine import Pin, SPI
from os import uname


class MFRC522:
    # Status codes
    OK = 0
    NOTAGERR = 1
    ERR = 2

    # Card commands
    REQIDL = 0x26
    REQALL = 0x52
    AUTHENT1A = 0x60
    AUTHENT1B = 0x61

    def __init__(self, sck, mosi, miso, rst, cs, spi_id=0, baudrate=1000000):
        # Set up SPI pins and reset the reader.
        self.sck = Pin(sck, Pin.OUT)
        self.mosi = Pin(mosi, Pin.OUT)
        self.miso = Pin(miso, Pin.IN)
        self.rst = Pin(rst, Pin.OUT)
        self.cs = Pin(cs, Pin.OUT)

        self.cs.value(1)
        self.rst.value(0)
        self.rst.value(1)

        board = uname().sysname
        if board == "WiPy":
            raise RuntimeError("This driver is not set up for WiPy.")
        else:
            self.spi = SPI(
                spi_id,
                baudrate=baudrate,
                polarity=0,
                phase=0,
                sck=self.sck,
                mosi=self.mosi,
                miso=self.miso
            )

        self.init()

    def _wreg(self, reg, val):
        # Write one byte to a register.
        self.cs.value(0)
        self.spi.write(bytearray([(reg << 1) & 0x7E]))
        self.spi.write(bytearray([val]))
        self.cs.value(1)

    def _rreg(self, reg):
        # Read one byte from a register.
        self.cs.value(0)
        self.spi.write(bytearray([((reg << 1) & 0x7E) | 0x80]))
        val = self.spi.read(1)
        self.cs.value(1)
        return val[0]

    def _sflags(self, reg, mask):
        # Set bits in a register.
        self._wreg(reg, self._rreg(reg) | mask)

    def _cflags(self, reg, mask):
        # Clear bits in a register.
        self._wreg(reg, self._rreg(reg) & (~mask))

    def _tocard(self, cmd, send):
        # Send a command and data to the RFID card.
        recv = []
        bits = 0
        irq_en = 0x00
        wait_irq = 0x00
        stat = self.ERR

        if cmd == 0x0E:  # PCD_AUTHENT
            irq_en = 0x12
            wait_irq = 0x10
        elif cmd == 0x0C:  # PCD_TRANSCEIVE
            irq_en = 0x77
            wait_irq = 0x30

        self._wreg(0x02, irq_en | 0x80)
        self._cflags(0x04, 0x80)
        self._sflags(0x0A, 0x80)
        self._wreg(0x01, 0x00)

        for c in send:
            self._wreg(0x09, c)

        self._wreg(0x01, cmd)

        if cmd == 0x0C:
            self._sflags(0x0D, 0x80)

        i = 2000
        while True:
            n = self._rreg(0x04)
            i -= 1
            if not ((i != 0) and not (n & 0x01) and not (n & wait_irq)):
                break

        self._cflags(0x0D, 0x80)

        if i != 0:
            if (self._rreg(0x06) & 0x1B) == 0x00:
                stat = self.OK

                if n & irq_en & 0x01:
                    stat = self.NOTAGERR

                if cmd == 0x0C:
                    n = self._rreg(0x0A)
                    lbits = self._rreg(0x0C) & 0x07
                    if lbits != 0:
                        bits = (n - 1) * 8 + lbits
                    else:
                        bits = n * 8

                    if n == 0:
                        n = 1
                    if n > 16:
                        n = 16

                    for _ in range(n):
                        recv.append(self._rreg(0x09))
            else:
                stat = self.ERR

        return stat, recv, bits

    def _crc(self, data):
        # Calculate CRC for a data packet.
        self._cflags(0x05, 0x04)
        self._sflags(0x0A, 0x80)

        for c in data:
            self._wreg(0x09, c)

        self._wreg(0x01, 0x03)

        i = 0xFF
        while True:
            n = self._rreg(0x05)
            i -= 1
            if not ((i != 0) and not (n & 0x04)):
                break

        return [self._rreg(0x22), self._rreg(0x21)]

    def init(self):
        # Initialize the RFID reader chip.
        self.reset()
        self._wreg(0x2A, 0x8D)
        self._wreg(0x2B, 0x3E)
        self._wreg(0x2D, 30)
        self._wreg(0x2C, 0)
        self._wreg(0x15, 0x40)
        self._wreg(0x11, 0x3D)
        self.antenna_on()

    def reset(self):
        # Reset the reader.
        self._wreg(0x01, 0x0F)

    def antenna_on(self, on=True):
        # Turn the antenna on or off.
        if on and ~(self._rreg(0x14) & 0x03):
            self._sflags(0x14, 0x03)
        else:
            self._cflags(0x14, 0x03)

    def request(self, mode):
        # Look for a nearby card.
        self._wreg(0x0D, 0x07)
        stat, recv, bits = self._tocard(0x0C, [mode])

        if (stat != self.OK) or (bits != 0x10):
            stat = self.ERR

        return stat, bits

    def anticoll(self):
        # Run anti-collision and read the card UID.
        ser_chk = 0
        ser = [0x93, 0x20]

        self._wreg(0x0D, 0x00)
        stat, recv, bits = self._tocard(0x0C, ser)

        if stat == self.OK:
            if len(recv) == 5:
                for i in range(4):
                    ser_chk ^= recv[i]
                if ser_chk != recv[4]:
                    stat = self.ERR
            else:
                stat = self.ERR

        return stat, recv

    def select_tag(self, ser):
        # Select a tag after its UID has been read.
        buf = [0x93, 0x70] + ser[:5]
        buf += self._crc(buf)
        stat, recv, bits = self._tocard(0x0C, buf)

        if (stat == self.OK) and (bits == 0x18):
            return self.OK
        return self.ERR

    def auth(self, mode, addr, sect, ser):
        # Authenticate before accessing a block.
        return self._tocard(0x0E, [mode, addr] + sect[:6] + ser[:4])[0]

    def stop_crypto1(self):
        # Stop encrypted communication.
        self._cflags(0x08, 0x08)

    def read(self, addr):
        # Read one 16-byte block.
        data = [0x30, addr]
        data += self._crc(data)
        stat, recv, _ = self._tocard(0x0C, data)

        if stat == self.OK:
            if len(recv) == 16:
                return recv
        return None

    def write(self, addr, data):
        # Write one 16-byte block.
        buf = [0xA0, addr]
        buf += self._crc(buf)
        stat, recv, bits = self._tocard(0x0C, buf)

        if not (stat == self.OK and bits == 4 and (recv[0] & 0x0F) == 0x0A):
            return self.ERR

        buf = data[:16]
        while len(buf) < 16:
            buf.append(0)
        buf += self._crc(buf)

        stat, recv, bits = self._tocard(0x0C, buf)
        if stat == self.OK and bits == 4 and (recv[0] & 0x0F) == 0x0A:
            return self.OK
        return self.ERR
