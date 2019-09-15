# https://www.analog.com/media/en/technical-documentation/data-sheets/AD7147.pdf
# 13 channel CapTouch Programmable Controller for Single-Electrode Capacitance Sensors

'''
IC expects particular start-up sequence:
	- calibration values are populated
	- stages are set up and defined
	- general IC setup
	- measurement

'''


from enum import Enum
import logging

from devices.utils import merge_bytes, set_bits_in_byte_16

I2C_ADDRESS_BASE = 0x2c
I2C_ADDRESS_COUNT = 4

# register address mappings
REG_PWR_CONTROL = 0x0000
REG_CHIP_ID = 0x017
REG_STAGE_CONFIG_BASE = 0x080
REG_STAGE_RESULT_BASE = 0x00B
REG_STAGE_RESULT_RAW_BASE = 0x0E0
REG_STAGE_RESULT_AVG_MAX = 0x0F9
REG_STAGE_RESULT_AVG_MIN = 0x100
REG_STAGE_RESULT_SF_AMBIENT = 0x0F2

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
		self.read_status()

	def get_chip_id(self):
		if self.chip_id == 0:
			response = self._read_reg(REG_CHIP_ID, 2)
			self.chip_id = merge_bytes(response) >> 4
			self.chip_revision = response[1] & 0x0F
		return self.chip_id

	def get_chip_revision(self):
		self.get_chip_id()
		return self.chip_revision

	def read_status(self):
		response = merge_bytes(self._read_reg(REG_PWR_CONTROL, 2))
		self.power_status = AD7147.ConfigurationReg.parseRaw(response)

	def set_power_mode(self, mode):
		self.power_status.power_mode = mode
		self._update_power_reg()

	# number of stages in a sequence is 0-based, meaning 0 == 1, 1 == 2, etc
	def set_sequence_stage_number(self, count):
		self.power_status.sequence_stage_count = count -1
		self._update_power_reg()

	def set_conversion_delay(self, delay):
		self.power_status.conversion_delay = delay
		self._update_power_reg()

	def set_stage_config(self, config):
		stage_base_address = REG_STAGE_CONFIG_BASE + config._id *8
		# set all pins to not connected by default
		conn_reg_lo = 0b00111111111111
		# same for other pins, disable offsets, do not use single ended
		conn_reg_hi = 0b1100111111111111
		for p in config._pins:
			if 6 >= p._pin_no:
				conn_reg_lo = set_bits_in_byte_16(conn_reg_lo, p._pin_no*2, p._connection_type.value, target_width=2)
			else:
				conn_reg_hi = set_bits_in_byte_16(conn_reg_hi, (p._pin_no-7)*2, p._connection_type.value, target_width=2)
		out = [conn_reg_lo >> 8, conn_reg_lo & 0xFF, conn_reg_hi >> 8, conn_reg_hi & 0xFF]
		self._write_reg(stage_base_address, out)

	def read_stage_value(self, stage):
		stage_address = REG_STAGE_RESULT_BASE + stage._id
		return merge_bytes(self._read_reg(stage_address, 2))

	def read_stage_value_raw(self, stage):
		stage_address_raw = REG_STAGE_RESULT_RAW_BASE + stage._id *36
		return merge_bytes(self._read_reg(stage_address_raw, 2))

	def read_stage_value_avg_max(self, stage):
		addr = REG_STAGE_RESULT_AVG_MAX + stage._id *36
		return merge_bytes(self._read_reg(addr, 2))

	def read_stage_value_avg_min(self, stage):
		addr = REG_STAGE_RESULT_AVG_MIN + stage._id *36
		return merge_bytes(self._read_reg(addr, 2))

	def read_stage_value_slow_fifo_ambient(self, stage):
		addr = REG_STAGE_RESULT_SF_AMBIENT + stage._id *36
		return merge_bytes(self._read_reg(addr, 2))


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
		self._write_fn(None, out)


	'''
	Chip power configuration register is shadowed locally in main class
	'''
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


'''
Device has 12 stages, each can be configured differently and they can share pins between them. 
Measurement sequence is considered done, when all the stages are completed. 
'''
class Stage:
	_ic = None
	_id = -1
	_pins = None
	connection_mode = None

	def __init__(self, ic, id):
		if not (0 <= id <= 12):
			raise ValueError('Stage id out of range')
		self._ic = ic
		self._id = id
		self._pins = list()
		self.connection_mode = Stage.ConnectionMode.POSITIVE_INPUT

	def setup_connection(self, mode):
		self.connection_mode = mode

	def assign_pins(self, pins: list):
		self._pins = pins

	def commit(self):
		self._ic.set_stage_config(self)

	def read_value(self):
		return self._ic.read_stage_value(self)

	def read_value_raw(self):
		return self._ic.read_stage_value_raw(self)

	# no idea what these 3 should do, but seem to contain static numbers
	def read_value_avg_min(self):
		return self._ic.read_stage_value_avg_min(self)

	def read_value_avg_max(self):
		return self._ic.read_stage_value_avg_max(self)

	def read_slow_ambient(self):
		return self._ic.read_stage_value_slow_fifo_ambient(self)
	class StagePin:
		class ConnectionType(Enum):
			NOT_CONNECTED = 0b00
			SINGLE_ENDED_NEGATIVE = 0b01
			SINGLE_ENDED_POSITIVE = 0b10
			BIASED = 0b11

		_pin_no = -1
		_connection_type = ConnectionType.NOT_CONNECTED

		def __init__(self, pin_no, connection_type):
			if not (0 <= pin_no <= 12):
				raise ValueError('Pin number %d out of range' %pin_no)
			self._pin_no = pin_no
			self._connection_type = connection_type



	'''
	Apparently whole chip should be configured in the same manner in a stage, these 2 bits define this manner 
	'''
	class ConnectionMode(Enum):
		# this should not be used
		FORBIDDEN = 0b00
		POSITIVE_INPUT = 0b01
		NEGATIVE_INPUT = 0b10
		DIFFERENTIAL = 0b11

	'''
	If at least one pin is used in single-ended mode, then this must be set
	'''
	class SingleEndedConnectionSetup(Enum):
		DO_NOT_USE = 0b00
		USE_WHEN_POS = 0b01
		USE_WHEN_NEG = 0b10
		DIFFERENTIAL = 0b11

