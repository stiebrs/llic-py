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


# pyftdi.i2c provides capability to poll any bus address to check for device presence
def poll(bus):
	for i in range(0x79):
		r = bus.poll(i)
		if r:
			print(hex(i))


def merge_bytes(arr):
	return arr[0] << 8 | arr[1]


def clear_bits_in_byte(source, index, bit_count, max_width):
	return (source & ~(pow(2, bit_count)-1 << index) & pow(2, max_width)-1)


def set_bits_in_byte(source, lsb_index, target, max_width, t_width=None):
	if not t_width:
		t_width = target.bit_length()
	return (clear_bits_in_byte(source, lsb_index, t_width, max_width) | (target << (lsb_index)) & pow(2, max_width)-1)


def set_bits_in_byte_8(source, lsb_index, target, target_width=None):
	return set_bits_in_byte(source, lsb_index, target, 8, target_width)


def set_bits_in_byte_16(source, lsb_index, target, target_width=None):
	return set_bits_in_byte(source, lsb_index, target, 16, target_width)
