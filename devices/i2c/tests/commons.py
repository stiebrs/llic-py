import logging


def get_i2c_read_fn(port, logger=logging.getLogger()):
	def return_fn(reg, num_bytes):
		port.flush()
		logger.debug('Out: [%s], expect: %d', hex(reg), num_bytes)
		val = port.read_from(reg, num_bytes)
		logger.debug('Resp: [{}]'.format(','.join(hex(x) for x in val)))
		return val

	return return_fn


def get_i2c_write_fn(port):
	def return_fn(reg, data):
		port.flush()
		port.write_to(reg, out=bytes(data))

	return return_fn
