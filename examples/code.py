# SPDX-FileCopyrightText: 2024 TimoKsn 
# SPDX-License-Identifier: MIT

# https://github.com/timoksn/Tinyvisionai_CircuitPython_PicoIce

#  usage:
#       1)  install https://circuitpython.org/board/pimoroni_pga2350 on your pico-ice (tested with CircuitPython 9.2.1)
#       2)  copy tinyvisionai_picoice.py to circuitpython drive (https://github.com/timoksn/Tinyvisionai_CircuitPython_PicoIce/blob/main/tinyvisionai_picoice.py)
#       3)  copy or create this file (code.py) to circuitpython drive  (https://github.com/timoksn/Tinyvisionai_CircuitPython_PicoIce/blob/main/examples/code.py)
#       4)  copy an ICE gateware bin file (top.bin) to circuitpython drive (blinky example: https://github.com/timoksn/Tinyvisionai_CircuitPython_PicoIce/blob/main/examples/top.bin)
#           this will flash the bin file every time pico resets. Delete the .bin file if you don't need this to be done everytime.
import tinyvisionai_picoice

iceprog = tinyvisionai_picoice.iceprog("pico2-ice") #pass pico-ice version to handle different pin configuration
iceprog.program_fpga("top.bin")   #flash gateware
iceprog.start_fpga(12000000) #run fpga with pico generated clock speed


while True:
    pass
