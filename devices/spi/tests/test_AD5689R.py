#!/usr/bin/env python3
import logging

import sys

import os

from pyftdi.spi import SpiController

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from devices.spi.AD5689R import AD5689

spi = SpiController(cs_count=1)
spi.configure('ftdi://ftdi:232h:/1')
spi_port = spi.get_port(cs=0, freq=10e6, mode=1)


def write_fn(binary_data):
    spi_port.write(binary_data)


if __name__ == '__main__':
    logging.basicConfig()
    log = logging.getLogger("test")
    log_dev = logging.getLogger("AD5689")
    log_dev.setLevel(logging.DEBUG)

    DAC = AD5689(write_fn, reference_gain=2)
    DAC.power_down_channel(AD5689.DAC_Channel.DAC_B, power_down_mode=AD5689.DAC_PowerDownMode.POWER_DOWN_MODE_1k_TO_GND)
    DAC.set_channel_and_update(AD5689.DAC_Channel.DAC_A, 0.35)
    input("Press Enter once stabilized")
    DAC.set_channel_and_update(AD5689.DAC_Channel.DAC_B, 0.2)
    DAC.power_down_channel(AD5689.DAC_Channel.DAC_B, power_down_mode=AD5689.DAC_PowerDownMode.POWER_DOWN_MODE_ON)
    input("Press Enter once done")
    DAC.power_down_channel(AD5689.DAC_Channel.DAC_B, power_down_mode=AD5689.DAC_PowerDownMode.POWER_DOWN_MODE_1k_TO_GND)
    DAC.set_channel_and_update(AD5689.DAC_Channel.DAC_A, 0.75)
    spi.terminate()
