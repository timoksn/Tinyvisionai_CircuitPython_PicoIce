# SPDX-FileCopyrightText: 2024 timoksn
# SPDX-License-Identifier: MIT
#               Michael Bell - Original micropython code
#               TimoKsn - port to circuitpython and added more funtionality

import time
import board
import digitalio
import busio
import os
import pwmio

__version__ = "0.0.0.1"
__repo__ = "https://github.com/timoksn/Tinyvisionai_CircuitPython_PicoIce"


#flash commands
CMD_WRITE = 0x02
CMD_READ = 0x03
CMD_READ_SR1 = 0x05
CMD_WEN = 0x06
CMD_SECTOR_ERASE = 0x20
CMD_ID = 0x90
CMD_RELEASE_POWER_DOWN = 0xAB

class iceprog:
    """ICE Flash programmer for pico-ice"""
    def __init__(self, picoice_version=None):
        self.picoice_version = picoice_version #TODO: to handle pico-ice or pico2-ice pin configuration. Default pico2-ice

    def initiliaze_pins(self):
        # Initialize pins and set them to input mode with no pull
        for i in range(47):
            try:
                pin = digitalio.DigitalInOut(getattr(board, f"IO{i}"))
                pin.direction = digitalio.Direction.INPUT
                pin.pull = None
            except AttributeError:
                # Skip invalid pins that are not defined in the board module
                pass

    def flash_cmd(self,data, dummy_len=0, read_len=0):
        dummy_buf = bytearray(dummy_len)
        read_buf = bytearray(read_len)

        self.flash_sel.value = False
        while not self.spi.try_lock():
            pass
        self.spi.write(bytearray(data))
        if dummy_len > 0:
            self.spi.readinto(dummy_buf)
        if read_len > 0:
            self.spi.readinto(read_buf)
        self.spi.unlock()
        self.flash_sel.value = True

        return read_buf

    def flash_cmd2(self,data, data2):
        self.flash_sel.value = False
        while not self.spi.try_lock():
            pass
        self.spi.write(bytearray(data))
        self.spi.write(data2)
        self.spi.unlock()
        self.flash_sel.value = True

    def print_bytes(self,data):
        for b in data:
            print("%02x " % (b,), end="")
        print()

    def flash_fpga(self, filename):
        print("Flashing FPGA gateware:" + filename)
        # Initialize SPI
        #self.spi = busio.SPI(clock=board.GP6, MOSI=board.GP7, MISO=board.GP4)

        # Flash select pin
        #self.flash_sel = digitalio.DigitalInOut(board.GP5)
        self.flash_sel.direction = digitalio.Direction.OUTPUT
        self.flash_sel.value = True

        # Wake up the flash
        self.flash_cmd([CMD_RELEASE_POWER_DOWN])
        time.sleep(1)

        print("Flash ID")
        id = self.flash_cmd([CMD_ID], 2, 3)
        self.print_bytes(id)

        with open(filename, "rb") as f:
            buf = bytearray(4096)
            sector = 0
            while True:
                num_bytes = f.readinto(buf)
                if num_bytes == 0:
                    break

                self.flash_cmd([CMD_WEN])
                self.flash_cmd([CMD_SECTOR_ERASE, sector >> 4, (sector & 0xF) << 4, 0])

                while self.flash_cmd([CMD_READ_SR1], 0, 1)[0] & 1:
                    print("*", end="")
                    time.sleep(0.01)
                print(".", end="")

                for i in range(0, num_bytes, 256):
                    self.flash_cmd([CMD_WEN])
                    self.flash_cmd2([CMD_WRITE, sector >> 4, ((sector & 0xF) << 4) + (i >> 8), 0], buf[i:min(i+256, num_bytes)])
                    while self.flash_cmd([CMD_READ_SR1], 0, 1)[0] & 1:
                        print("-", end="")
                        time.sleep(0.01)
                print(".")
                sector += 1

        with open(filename, "rb") as f:
            data = bytearray(256)
            i = 0
            while True:
                num_bytes = f.readinto(data)
                if num_bytes == 0:
                    break

                data_from_flash = self.flash_cmd([CMD_READ, i >> 8, i & 0xFF, 0], 0, num_bytes)
                for j in range(num_bytes):
                    if data[j] != data_from_flash[j]:
                        raise Exception(f"Error at {i:02x}:{j:02x}: {data[j]} != {data_from_flash[j]}")
                i += 1

        print("flash verify done")
        data_from_flash = self.flash_cmd([CMD_READ, 0, 0, 0], 0, 16)
        self.print_bytes(data_from_flash)

    def stop_fpga(self):
        try:
            self.ice_creset = digitalio.DigitalInOut(board.GP31)
        except:
            self.ice_creset.deinit()
            self.ice_creset = digitalio.DigitalInOut(board.GP31)    
            
        self.ice_creset.direction = digitalio.Direction.OUTPUT

        print("stopping fpga")
        self.ice_creset.value = 0
        time.sleep(1)
        
        self.ice_creset.deinit()
        
    
    def start_fpga(self, clk_speed:None):
    
        print(">starting fpga   ")    
        pwm = pwmio.PWMOut(board.GP1, duty_cycle=2 ** 15, frequency=clk_speed, variable_frequency=False)
        
        try:
            self.ice_done = digitalio.DigitalInOut(board.GP40)
        except:
            self.ice_done.deinit()
            self.ice_done = digitalio.DigitalInOut(board.GP40)
        
        self.ice_done.direction = digitalio.Direction.INPUT
        
        try:
            self.ice_creset = digitalio.DigitalInOut(board.GP31)
        except:
            self.ice_creset.deinit()
            self.ice_creset = digitalio.DigitalInOut(board.GP31)
            
        self.ice_creset.direction = digitalio.Direction.OUTPUT
        self.ice_creset.value = 1
        time.sleep(0.5)
        
        while not self.ice_done.value:
            print(".", end="")
            time.sleep(0.001)
            
        print("<starting")
        print("FPGA State:" + str(self.ice_done.value))
        
                
    def program_fpga(self, filename) -> None:
        try:
            os.stat(filename)
            FILE_EXISTS = True
        except:
            FILE_EXISTS = False

        self.initiliaze_pins()
        self.stop_fpga()
        
        if FILE_EXISTS:
            self.spi = busio.SPI(clock=board.GP6, MOSI=board.GP7, MISO=board.GP4)
            self.flash_sel = digitalio.DigitalInOut(board.GP5)
            self.flash_fpga(filename)
            self.flash_sel.deinit()

