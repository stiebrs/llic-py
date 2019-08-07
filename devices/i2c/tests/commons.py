import logging


def get_i2c_read_fn(port, logger=logging.getLogger()):
	def return_fn(reg, num_bytes):
		port.flush()
		logger.debug('>: [{}], expect %d'.format(','.join(hex(x) for x in reg)) % num_bytes)
		val = port.exchange(reg, num_bytes)
		logger.debug('Resp: [{}]'.format(','.join(hex(x) for x in val)))
		return val

	return return_fn


def get_i2c_write_fn(port):
	def return_fn(reg, data):
		port.flush()
		# port.write_to(reg, out=bytes(data))
		if reg:
			out = list([reg]).append(data)
		else:
			out = data
		port.exchange(out, readlen=1)

	return return_fn


def merge_bytes(arr):
	return arr[0] << 8 | arr[1]


# pyftdi.i2c provides capability to poll any bus address to check for device presence
def poll(bus):
	for i in range(0x79):
		r = bus.poll(i)
		if r:
			print(hex(i))
