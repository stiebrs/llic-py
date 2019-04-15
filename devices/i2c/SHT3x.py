# based on https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/0_Datasheets/Humidity/Sensirion_Humidity_Sensors_SHT3x_Datasheet_digital.pdf
# tested with FT232H MPSEE module

import logging

# SHT3x-DIS default address (ADDR pulled to VSS (ground))
import struct

SHT3x_I2CADDR = 0x44
# SHT3x-DIS alternative address (ADDR pulled to VDD (supply))
SHT3x_I2CADDR_ALT = 0x45

# SHT3x-DIS Registers
# @TODO: implement all the functionality

class SHT3x:
	_readFn = None
	_writeFn = None
	_log = None
	_continuous_mode = False

	def __init__(self, readFn, writeFn):
		self._log = logging.getLogger('SHT3x')
		self._readFn = readFn
		self._writeFn = writeFn

	def enable_continuous_mode(self, mps=1, repeatability='HIGH'):
		regVal = 0x21 << 8 | 0x30
		self._writeReg(regVal)
		self._continuous_mode = True

	def get_temp_humidity(self):
		if self._continuous_mode:
			self._writeReg(0xE000)

		resp = self._readBus(6)
		t_raw, t_crc, h_raw, h_crc = struct.unpack('>HBHB', resp)
		if crc8(resp[:2]) != t_crc:
			self._log.warning('Bad CRC for temperature')
		if crc8(resp[3:5]) != h_crc:
			self._log.warning('Bad CRC for humidity')
		temp = (175.0 * (t_raw / 0xFFFF)) - 45.0
		h = 100.0 * (h_raw / 0xFFFF)
		return temp, h


	def _readReg(self, reg, numBytes):
		self._log.debug('>: [%s], expect: %d', hex(reg), numBytes)
		self._writeReg(reg)
		val = self._readBus(numBytes)
		return val

	def _readBus(self, numBytes):
		val = self._readFn(numBytes)
		self._log.debug('<: [{}]'.format(','.join(hex(x) for x in val)))
		return val

	def _writeReg(self, cmd):
		self._log.debug('>: [%s]', hex(cmd))
		self._writeFn([cmd >> 8, cmd & 0xFF])

def crc8(buffer):
	""" Polynomial 0x31 (x8 + x5 +x4 +1) """
	polynomial = 0x31
	crc = 0xFF

	for index in range(0, len(buffer)):
		crc ^= buffer[index]
		for i in range(8, 0, -1):
			if crc & 0x80:
				crc = (crc << 1) ^ polynomial
			else:
				crc = (crc << 1)

	return crc & 0xFF