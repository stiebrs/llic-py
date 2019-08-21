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
