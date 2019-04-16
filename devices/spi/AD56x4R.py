'''
Constructor expects only write function
Tested with AD5664R-5 both with external and internal references
By default on power-up internal reference is disabled, call enableInternalRef() to enable it.
Outputs will not change until some sort of reference is passed in.
'''

import logging
from enum import Enum


class Command(Enum):
	CMD_WRITE_REG_N = 0x00
	CMD_UPDATE_REG_N = 0x01
	CMD_WRITE_N_UPDATE_ALL = 0x02
	CMD_WRITE_AND_UPDATE_N = 0x03
	CMD_PWR_UP_DOWN = 0x04
	CMD_RESET = 0x05
	CMD_LDAC_SETUP = 0x06
	CMD_INTERNAL_REF = 0x07


class Channel(Enum):
	A = 0x00
	B = 0x01
	C = 0x02
	D = 0x03
	ALL = 0x07


CMD_POS = 19
ADDR_POS = 16


class DAC:
	_writeFn = None
	LSB = 0.0
	log = None

	'''
	User has to init/deinit SPI bus themselves and provide only
	write function, which accepts byte array.
	refVal as float reference voltage value (default 1.25 or 2.5 for AD56x4R-5)
	resolution in bits (together with refVal used to calculate LSB value)
	externalRef boolean True if external or internal reference is used
	'''
	def __init__(self, writeFn, refVal=1.25, resolution=16, externalRef=False):
		self._writeFn = writeFn
		self.log = logging.getLogger('AD56x4R')
		if externalRef:
			self.LSB = refVal / pow(2, resolution)
		else:
			self.LSB = refVal / pow(2, resolution) * 2

	def enableInternalRef(self):
		self._writeData('CMD_INTERNAL_REF', 0x01)

	def disableInternalRef(self):
		self._writeData('CMD_INTERNAL_REF', 0x00)

	def reset(self):
		self._writeData('CMD_RESET', 0x01)

	def setOutput(self, channel: Channel, voltage):
		binVal = round(voltage / self.LSB)
		self._writeData('CMD_WRITE_AND_UPDATE_N', binVal, channel.value)

	# split data into bytes, shuffle along commands and addresses
	def _writeData(self, cmd, val, channel=0):
		data = Command[cmd].value << CMD_POS | channel << ADDR_POS | val
		d = [(data >> 16) & 0xFF, (data >> 8) & 0xFF, data & 0xFF]
		self.log.debug('>: [{}]'.format(','.join(hex(x) for x in d)))
		self._writeFn(d)
