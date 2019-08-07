#!/usr/bin/env python3

import pyftdi.i2c
import AD7156
import commons


def print_cdc_status():
	cdc.read_status()
	print('Power on: %s' % cdc.powered_on)
	print('Last measured channel: %d, channel 1 data available: %s, channel 2 data available: %s' % (cdc.ch_last_converted, cdc.ch1_data_ready, cdc.ch2_data_ready))
	print('CAPDAC changed for channel 1: %s, channel 2: %s' % (cdc.ch1_CAPDAC_changed, cdc.ch2_CAPDAC_changed))
	print('Threshold exceeded for channel 1: %s, channel 2: %s' % (cdc.ch1_threshold_crossed, cdc.ch2_threshold_crossed))


i2cController = pyftdi.i2c.I2cController()
i2cController.configure('ftdi://ftdi:2232h/1')

try:
	# pass
	port = i2cController.get_port(AD7156.I2C_ADDRESS)
	# print(port.exchange([AD7156.REG_CHIP_ID], 1))
	cdc = AD7156.AD7156(commons.get_i2c_read_fn(port), commons.get_i2c_write_fn(port))
	print('Chip ID: %s, sn: %s' % (hex(cdc.get_chip_id()), hex(cdc.get_chip_sn())))
	print_cdc_status()
	print(cdc.read_value_pf(AD7156.Channel.Channel1))
	print(cdc.read_value_pf(AD7156.Channel.Channel2))
	print_cdc_status()
	print(cdc.get_threshold_in_pf(AD7156.Channel.Channel1))
	print(cdc.get_threshold_in_pf(AD7156.Channel.Channel2))
	cdc.set_threshold_in_pf(AD7156.Channel.Channel1, 1.00)
	print(cdc.get_threshold_in_pf(AD7156.Channel.Channel1))

finally:
	i2cController.terminate()


