# https://www.analog.com/media/en/technical-documentation/data-sheets/AD7156.pdf
# 2 channel CDC

from enum import Enum
import logging

from commons import merge_bytes

I2C_ADDRESS = 0x48
# address mappings
REG_STATUS = 0x00
REG_CH1_DATA_HI = 0x01
REG_CH1_DATA_LO = 0x02
REG_CH2_DATA_HI = 0x03
REG_CH2_DATA_LO = 0x04
REG_CH1_AVG_HI = 0x05
REG_CH1_AVG_LO = 0x06
REG_CH2_AVG_HI = 0x07
REG_CH2_AVG_LO = 0x08
REG_CH1_SENS_THR_HI = 0x09
REG_CH1_SENS_THR_LO = 0x0A
REG_CH1_SETUP = 0x0B
REG_CH2_SENS_THR_HI = 0x0C
REG_CH2_SENS_THR_LO = 0x0D
REG_CH2_SETUP = 0x0E
REG_CONFIG = 0x0F
REG_POWER_DOWN_TIMER = 0x10
REG_CH1_CAPDAC = 0x11
REG_CH2_CAPDAC = 0x12
REG_SN3 = 0x13
REG_SN2 = 0x14
REG_SN1 = 0x15
REG_SN0 = 0x16
REG_CHIP_ID = 0x17


class FullScale(Enum):
	FS_4PF = (0b11, 4.0)
	FS_2PF = (0b00, 2.0)
	FS_1PF = (0b10, 1.0)
	FS_05PF = (0b01, 0.5)


class SampleRate(Enum):
	RATE_1024 = 0b00
	RATE_256 = 0b01
	RATE_64 = 0b10
	RATE_8 = 0b11


class Channel(Enum):
	Channel1 = 0x00
	Channel2 = 0x01


class AD7156:

	readFn = None
	log = None
	# false, if in sleep mode
	powered_on = True
	# true, if during last coversion auto-DAC changed the offset for channel 1
	ch1_CAPDAC_changed = False
	ch1_threshold_crossed = False
	# true, if during last coversion auto-DAC changed the offset for channel 2
	ch2_CAPDAC_changed = False
	ch2_threshold_crossed = False
	ch_last_converted = 0
	ch1_data_ready = False
	ch2_data_ready = False
	full_scale = FullScale.FS_2PF

	'''
	readFn(addr, n) should read n bytes from the device register addr
	and return bytes
	'''
	def __init__(self, read_fn, write_fn):
		self._read_fn = read_fn
		self._write_fn = write_fn
		self.log = logging.getLogger('AD7156')

	def get_chip_id(self):
		return self._read_reg(REG_CHIP_ID, 1)[0]

	def get_chip_sn(self):
		response = self._read_reg(REG_SN0, 4)
		return response[0] << 24 | response[1] << 16 | response[2] << 8 | response[3] & 0xFF

	def read_status(self):
		response = self._read_reg(REG_STATUS, 1)[0]
		self.powered_on = not (response & 0x80)
		self.ch2_CAPDAC_changed = not (response & 0x40)
		self.ch2_threshold_crossed = bool(response & 0x20)
		self.ch1_CAPDAC_changed = not (response & 0x10)
		self.ch1_threshold_crossed = bool(response & 0x08)
		self.ch_last_converted = 2 if response & 0x04 else 1
		self.ch1_data_ready = not (response & 0x02)
		self.ch2_data_ready = not (response & 0x01)

	def convert_val_to_pf(self, val):
		return (val / 0xA000) * self.full_scale.value[1]

	def read_value_pf(self, channel: Channel):
		val = self.read_value_raw(channel)
		return self.convert_val_to_pf(val)

	def read_value_raw(self, channel: Channel):
		response = self._read_reg(REG_CH1_DATA_HI + channel.value*2, 2)
		val = merge_bytes(response) >> 4		# actual resolution is only 12 bits
		return val

	def set_threshold_in_pf(self, channel: Channel, value):
		if value > self.full_scale.value[1]:
			self.log.error("Attempt at setting too high threshold value: %3.6f, while full_scale is %3.6f", value, self.full_scale.value[1])
			return
		data = round(value / self.full_scale.value[1]/0xA000)
		data = data << 4
		self._write_reg(REG_CH1_SENS_THR_HI + channel.value*3, [data >> 8, data & 0xFF])

	def get_threshold_in_pf(self, channel: Channel):
		response = self._read_reg(REG_CH1_SENS_THR_HI + channel.value*3, 2)
		data = merge_bytes(response) >> 4
		return self.convert_val_to_pf(data)

	def _read_reg(self, reg, num_bytes):
		self.log.debug('>: [%s], expect: %d', hex(reg), num_bytes)
		val = self._read_fn(reg, num_bytes)
		self.log.debug('<: [{}]'.format(','.join(hex(x) for x in val)))
		return val

	def _write_reg(self, reg, data=[]):
		self.log.debug('>: [%s], data', hex(reg), data)
		self._write_fn(reg, data)
