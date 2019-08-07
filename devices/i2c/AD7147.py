# https://www.analog.com/media/en/technical-documentation/data-sheets/AD7147.pdf
# 13 channel CapTouch Programmable Controller for Single-Electrode Capacitance Sensors

from enum import Enum
import logging

from commons import merge_bytes

I2C_ADDRESS_BASE = 0x2c
I2C_ADDRESS_COUNT = 4

# register address mappings
REG_PWR_CONTROL = 0x0000
REG_CHIP_ID = 0x017


class AD7147:
	readFn = None
	log = None
	chip_id = 0
	chip_revision = 0
	power_status = None

	'''
	readFn(addr, n) should read n bytes from the device register addr
	and return bytes
	'''
	def __init__(self, read_fn, write_fn):
		self._read_fn = read_fn
		self._write_fn = write_fn
		self.log = logging.getLogger('AD7147')
		self.power_status = None

	def get_chip_id(self):
		if self.chip_id == 0:
			response = self._read_reg(REG_CHIP_ID, 2)
			self.chip_id = merge_bytes(response) >> 4
			self.chip_revision = response[1] & 0x0F
		return self.chip_id

	def get_chip_revision(self):
		self.get_chip_id()
		return self.chip_revision

	def get_chip_sn(self):
		# response = self._read_reg(REG_SN0, 4)
		# return response[0] << 24 | response[1] << 16 | response[2] << 8 | response[3] & 0xFF
		pass

	def read_status(self):
		response = merge_bytes(self._read_reg(REG_PWR_CONTROL, 2))
		self.power_status = AD7147.ConfigurationReg.parseRaw(response)

	def set_power_mode(self, mode):
		self.power_status.power_mode = mode
		self._update_power_reg()

	def set_sequence_stage_number(self, count):
		self.power_status.sequence_stage_count = count
		self._update_power_reg()

	def set_conversion_delay(self, delay):
		self.power_status.conversion_delay = delay
		self._update_power_reg()

	def _update_power_reg(self):
		reg = 0
		reg = reg | (self.power_status.conversion_delay.value << 2) | (self.power_status.sequence_stage_number << 4) \
			  | (self.power_status.ADC_decimation.value << 8) | (self.power_status.interrupt_polarity.value << 11) \
			  | (self.power_status.excitation_status.value << 12) | self.power_status.bias_current.value << 14 \
			  | (self.power_status.power_mode.value)
		self._write_reg(REG_PWR_CONTROL, [reg >> 8, reg & 0xFF])

	def _read_reg(self, reg, num_bytes):
		data = [reg >> 8, reg & 0xFF]
		val = self._read_fn(data, num_bytes)
		return val

	def _write_reg(self, reg, data=[]):
		# self.log.debug('>: [%s], data', hex(reg), data)
		out = list([reg >> 8, reg & 0xFF])
		out.extend(data)
		print(out)
		self._write_fn(None, out)

	class ConfigurationReg:
		power_mode = None
		conversion_delay = None
		sequence_stage_number = 0
		ADC_decimation = None
		interrupt_polarity = None
		excitation_status = None
		bias_current = None

		class PowerMode(Enum):
			FULL_POWER = 0b00
			LOW_POWER = 0b10
			SHUTDOWN = 0b01
			LOW_SHUTDOWN = 0b11

		class LowPowerConversionDelay(Enum):
			DELAY_200ms = 0b00
			DELAY_400ms = 0b01
			DELAY_600ms = 0b10
			DELAY_800ms = 0b11

		class ADCDecimationFactor(Enum):
			DECIMATE_256 = 0b00
			DECIMATE_128 = 0b01
			DECIMATE_64 = 0b10

		class InterruptPolarity(Enum):
			ACTIVE_LOW = 0b00
			ACTIVE_HI = 0b01

		# Enable excitation to CINx Pin
		class ExcitationStatus(Enum):
			ENABLE = 0b00
			DISABLE = 0b01

		class CDCBiasCurrent(Enum):
			NORMAL = 0b00
			NORMAL_20pct = 0b01
			NORMAL_35pct = 0b10
			NORMAL_50pct = 0b11

		@classmethod
		def parseRaw(cls, data):
			reg = AD7147.ConfigurationReg()
			reg.power_mode = AD7147.ConfigurationReg.PowerMode(data & 0b11)
			reg.conversion_delay = AD7147.ConfigurationReg.LowPowerConversionDelay((data >> 2) & 0b11)
			reg.sequence_stage_number = (data >> 4) & 0b1111
			reg.ADC_decimation = AD7147.ConfigurationReg.ADCDecimationFactor((data >> 8) & 0b11)
			reg.interrupt_polarity = AD7147.ConfigurationReg.InterruptPolarity((data >> 11) & 0b1)
			reg.excitation_status = AD7147.ConfigurationReg.ExcitationStatus((data >> 12) & 0b1)
			reg.bias_current = AD7147.ConfigurationReg.CDCBiasCurrent((data >> 14) & 0b11)
			return reg

