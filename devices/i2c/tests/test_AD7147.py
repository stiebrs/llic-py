#!/usr/bin/env python3
import logging

import pyftdi.i2c
import time

from AD7147 import AD7147, Stage, I2C_ADDRESS_BASE
import commons


def print_cdc_status():
	cdc.read_status()
	print('Power on: %s' % cdc.powered_on)
	print('Last measured channel: %d, channel 1 data available: %s, channel 2 data available: %s' % (cdc.ch_last_converted, cdc.ch1_data_ready, cdc.ch2_data_ready))
	print('CAPDAC changed for channel 1: %s, channel 2: %s' % (cdc.ch1_CAPDAC_changed, cdc.ch2_CAPDAC_changed))
	print('Threshold exceeded for channel 1: %s, channel 2: %s' % (cdc.ch1_threshold_crossed, cdc.ch2_threshold_crossed))
logging.basicConfig()
log = logging.getLogger("test")
log_dev = logging.getLogger("AD7147")
log.setLevel(logging.DEBUG)

i2cController = pyftdi.i2c.I2cController()
i2cController.configure('ftdi://ftdi:2232h/1')

try:
	# commons.poll(i2cController)
	port = i2cController.get_port(I2C_ADDRESS_BASE)
	# # print(port.exchange([AD7156.REG_CHIP_ID], 1))
	cdc = AD7147(commons.get_i2c_read_fn(port, logger=log), commons.get_i2c_write_fn(port))
	print('Chip ID: %s, revision: %s' % (hex(cdc.get_chip_id()), hex(cdc.get_chip_revision())))
	cdc.read_status()
	print('Power: %s, conversion delay: %s, decimation: %s, excitation: %s, bias: %s' % \
		  (cdc.power_status.power_mode, cdc.power_status.conversion_delay, cdc.power_status.ADC_decimation, \
		   cdc.power_status.excitation_status, cdc.power_status.bias_current))

	# Try turing off, change settings
	cdc.set_power_mode(AD7147.ConfigurationReg.PowerMode.LOW_POWER)
	cdc.set_conversion_delay(AD7147.ConfigurationReg.LowPowerConversionDelay.DELAY_800ms)
	cdc.set_sequence_stage_number(5)
	cdc.read_status()
	print('Power: %s, conversion delay: %s, decimation: %s, excitation: %s, bias: %s, stage count: %d' % \
		  (cdc.power_status.power_mode, cdc.power_status.conversion_delay, cdc.power_status.ADC_decimation, \
		   cdc.power_status.excitation_status, cdc.power_status.bias_current, cdc.power_status.sequence_stage_number))

	# turn on and change settings again
	cdc.set_power_mode(AD7147.ConfigurationReg.PowerMode.FULL_POWER)
	cdc.set_conversion_delay(AD7147.ConfigurationReg.LowPowerConversionDelay.DELAY_200ms)
	cdc.set_sequence_stage_number(2)
	cdc.read_status()
	print('Power: %s, conversion delay: %s, decimation: %s, excitation: %s, bias: %s, stage count: %d' % \
		  (cdc.power_status.power_mode, cdc.power_status.conversion_delay, cdc.power_status.ADC_decimation, \
		   cdc.power_status.excitation_status, cdc.power_status.bias_current, cdc.power_status.sequence_stage_number))

	# now we create differential measurement stage on pins CIN0 and CIN1
	stage = Stage(cdc, 0)
	pins = list([
		Stage.StagePin(0, Stage.StagePin.ConnectionType.SINGLE_ENDED_POSITIVE),
		Stage.StagePin(1, Stage.StagePin.ConnectionType.SINGLE_ENDED_NEGATIVE),
		Stage.StagePin(12, Stage.StagePin.ConnectionType.SINGLE_ENDED_NEGATIVE),
	])
	stage.assign_pins(pins)
	stage.setup_connection(Stage.ConnectionMode.DIFFERENTIAL)
	stage.commit()
	while (1):
		print(stage.read_value())
		time.sleep(1)
finally:
	i2cController.terminate()


