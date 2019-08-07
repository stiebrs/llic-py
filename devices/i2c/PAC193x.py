# based on http://ww1.microchip.com/downloads/en/DeviceDoc/PAC1932-Data-Sheet-DS20005850C.pdf
# tested with PAC1934

from enum import Enum
import logging

# address mappings
from commons import merge_bytes

CMD_REFRESH = 0x00
REG_CTRL = 0x01
REG_ACC_COUNT = 0x02
REG_VPOW_ACC_BASE = 0x03
REG_VBUS_BASE = 0x07
REG_VSENSE_BASE = 0x0B
REG_VBUS_AVG_BASE = 0x0F
REG_VSENSE_AVG_BASE = 0x13
REG_VPOWER_BASE = 0x17
REG_CHANNEL_DIS = 0x1C
REG_NEG_PWR = 0x1D
CMD_REFRESH_G = 0x1E
CMD_REFRESH_V = 0x1F
REG_SLOW = 0x20
REG_CTRL_ACT = 0x21
REG_CHANNEL_DIS_ACT = 0x22
REG_NEG_PWR_ACT = 0x23
REG_CTRL_LAT = 0x24
REG_DISL_LAT = 0x25
REG_NEW_PWR_LAT = 0x26
REG_PRODUCT_ID = 0xFD
REG_MFR_ID = 0xFE
REG_REV_ID = 0xFF


class Revision(Enum):
	PAC1932 = 0b01011001
	PAC1933 = 0b01011010
	PAC1934 = 0b01011011


class SampleRate(Enum):
	RATE_1024 = 0b00
	RATE_256 = 0b01
	RATE_64 = 0b10
	RATE_8 = 0b11


class Channel(Enum):
	A = 0x00
	B = 0x01
	C = 0x02
	D = 0x03


class PAC193x:

	shunt1 = 1.0
	shunt2 = 1.0
	shunt3 = 1.0
	shunt4 = 1.0
	readFn = None
	log = None
	revision = None
	'''
	readFn(addr, n) should read n bytes from the device register addr
	and return bytes
	'''
	def __init__(self, read_fn, write_fn):
		self._read_fn = read_fn
		self._write_fn = write_fn
		self.log = logging.getLogger('PAC')
		self.check_device()

	def check_device(self):
		data = self._read_reg(REG_PRODUCT_ID, 3)
		if (0x59 <= data[0] <= 0x5B) and (data[1] == 0x5D) and (data[2] == 0x03):
			self.revision = Revision(data[0])
			return True, self.revision
		self.log.error('Could not find PAC193x with given address!')
		return False

	# shunt resistor values are used for current calculations
	def set_shunt_resistor_values(self, v1, v2, v3, v4):
		self.shunt1 = v1
		self.shunt2 = v2
		self.shunt3 = v3
		self.shunt4 = v4

	# returns bus voltage in V
	def get_bus_voltage(self, channel: Channel):
		return _parse_voltage(self._read_reg(REG_VBUS_BASE + channel.value, 2))

	def get_bus_voltage_average(self, channel: Channel):
		return _parse_voltage(self._read_reg(REG_VBUS_AVG_BASE + channel.value, 2))

	# returns sensed current in mA
	def get_current(self, channel: Channel):
		return _parse_current(self._read_reg(REG_VSENSE_BASE + channel.value, 2))

	def get_current_average(self, channel: Channel):
		return _parse_current(self._read_reg(REG_VSENSE_AVG_BASE + channel.value, 2))

	# refresh readout registers without resetting accumulators
	# should wait at least 1ms before reading out new values
	def refresh_v(self):
		self._write_reg(CMD_REFRESH_V, [])

	# refresh readout registers with resetting accumulators
	# should wait at least 1ms before reading out new values
	def refresh(self):
		self._write_reg(CMD_REFRESH, [])

	def set_sample_rate(self, sr: SampleRate):
		reg = self._read_control_reg()[0]
		reg = reg | (sr.value << 6)
		print('writing %s' % (hex(reg)))
		self._write_control_reg(reg)

	def get_sample_rate(self):
		reg = self._read_control_reg()[0]
		return SampleRate((reg & 0xFF) >> 6)

	def _read_control_reg(self):
		return self._read_reg(REG_CTRL, 1)

	def _write_control_reg(self, val):
		return self._write_reg(REG_CTRL, [val])

	def _read_reg(self, reg, numBytes):
		self.log.debug('>: [%s], expect: %d', hex(reg), numBytes)
		val = self._read_fn(reg, numBytes)
		self.log.debug('<: [{}]'.format(','.join(hex(x) for x in val)))
		return val

	def _write_reg(self, reg, data=[]):
		self.log.debug('>: [%s], data', hex(reg), data)
		self._write_fn(reg, data)


def _parse_voltage(data):
	adc_val = merge_bytes(data)
	return adc_val / pow(2, 16) * 32


def _parse_current(data):
	adc_val = merge_bytes(data)
	fsc = 0.1/1.0
	current = fsc * adc_val / pow(2, 16)
	return current
