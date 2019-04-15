#!/usr/bin/env python3

import pyftdi.i2c
import time

from PAC193x import Channel, SampleRate
from devices.i2c import PAC193x
from devices.i2c.tests import commons


def print_voltages_currents(dev: PAC193x):
	dev.refresh_v()
	with open('test_iv.csv', 'a') as f:
		# f.write('%3.6fV %3.6fA %3.6fV %3.6fA %3.6fV %3.6fA %3.6fV %3.6fA; AVGS: %3.6fV %3.6fA %3.6fV %3.6fA %3.6fV %3.6fA %3.6fV %3.6fA' % (
		f.write('%d %3.6f %3.6f %3.6f %3.6f %3.6f %3.6f %3.6f %3.6f %3.6f %3.6f %3.6f %3.6f %3.6f %3.6f %3.6f %3.6f\n' % (
			time.time(),
			dev.get_bus_voltage(Channel.A), dev.get_current(Channel.A),
			dev.get_bus_voltage(Channel.B), dev.get_current(Channel.B),
			dev.get_bus_voltage(Channel.C), dev.get_current(Channel.C),
			dev.get_bus_voltage(Channel.D), dev.get_current(Channel.D),
			dev.get_bus_voltage_average(Channel.A), dev.get_current_average(Channel.A),
			dev.get_bus_voltage_average(Channel.B), dev.get_current_average(Channel.B),
			dev.get_bus_voltage_average(Channel.C), dev.get_current_average(Channel.C),
			dev.get_bus_voltage_average(Channel.D), dev.get_current_average(Channel.D)
		))


i2cController = pyftdi.i2c.I2cController()
i2cController.configure('ftdi://ftdi:232h/1')


port = i2cController.get_port(16)
pac = PAC193x.PAC193x(commons.get_i2c_read_fn(port), commons.get_i2c_write_fn(port))
pac.set_sample_rate(SampleRate.RATE_64)
# print(pac.check_device())
try:
	while 1:
		print_voltages_currents(pac)
		time.sleep(5)
except:
	pass
finally:
	i2cController.terminate()
