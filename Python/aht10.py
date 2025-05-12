import time
import struct

class AHT10:
    def __init__(self, i2c, address=0x38):
        self.i2c = i2c
        self.address = address
        self._init_sensor()

    def _init_sensor(self):
        self.i2c.writeto(self.address, b'\xE1\x08\x00')
        time.sleep(0.05)

    def read(self):
        self.i2c.writeto(self.address, b'\xAC\x33\x00')
        time.sleep(0.5)
        data = self.i2c.readfrom(self.address, 6)
        if data[0] & 0x80:
            raise Exception("AHT10 not ready")

        raw_temp = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]
        raw_humi = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4

        temp = (raw_temp * 200.0 / 1048576.0) - 50
        humi = (raw_humi * 100.0) / 1048576.0
        return temp, humi
