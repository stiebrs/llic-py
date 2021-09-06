'''
Constructor expects only SPI write function, reference setup is optional
Tested with AD5689RxRZ with internal reference
By default on power-up internal reference is used.
Startup behavior is dependent on RSTSEL pin - tied to GND would start up at 0-scale, tied to V_Logic will start up mid-range
'''
import logging
from enum import Enum

class AD5689:

    class DAC_Command(Enum):
        CMD_NOP = 0x00
        CMD_WRITE_REG_N = 0x01
        CMD_UPDATE_DAC_N = 0x02
        CMD_WRITE_AND_UPDATE_N = 0x03
        CMD_PWR_UP_DOWN = 0x04
        CMD_LDAC_MASK = 0x05
        CMD_RESET = 0x06
        CMD_ENABLE_INTERNAL_REF = 0x07
        CMD_DCEN_EN_REG = 0x08
        CMD_READBACK_REG = 0x09
        CMD_NOP_DAISYCHAIN = 0x0F

    class DAC_Channel(Enum):
        DAC_A = 0x01
        DAC_B = 0x08
        DAC_BOTH = (DAC_A | DAC_B)

    _write_fn = None
    _gain = None

    '''
    Init expects:
     :param spi_write_fn: SPI write function, which should deal with appropriate CS toggling and actual SPI transmission
     :param reference_value: External voltage reference value. Defaults to internal 2.5V 
     :param reference_gain: Reference gain (pullup to V_Logic = x2, pulldown to GND = x1). Invalid values will default to x1
    '''
    def __init__(self, spi_write_fn, reference_value=2.5, reference_gain=1):
        self.log = logging.getLogger('AD5689')
        self._write_fn = spi_write_fn
        reference_gain = reference_gain if reference_gain == 2 else 1
        self._lsb = (reference_value * reference_gain) / pow(2, 16)

    def enable_internal_ref(self, enable=True):
        self._write_data(AD5689.DAC_Command.CMD_ENABLE_INTERNAL_REF, 0x00, enable)

    def set_channel_and_update(self, channel, voltage):
        self._write_data(AD5689.DAC_Command.CMD_WRITE_AND_UPDATE_N, channel, int(voltage/self._lsb))

    def set_channel_value(self, channel, voltage):
        self._write_data(AD5689.DAC_Command.CMD_WRITE_REG_N, channel, int(voltage / self._lsb))

    def update_channel_value(self, channel, voltage):
        self._write_data(AD5689.DAC_Command.CMD_UPDATE_DAC_N, channel, int(voltage / self._lsb))

    def _write_data(self, command, channel, data):
        '''
        24 bits (3 bytes) of data are sent.
        4 bits are command bits (DAC_Command)
        4 bits are Channel selection (DAC_Channel)
        16 bits are data bits for AD5689, 12 bits for AD5687 with last 4 bits DNC
        '''
        ba = bytearray([(command.value << 4) | channel.value, data >> 8, data & 0xFF])
        self.log.debug('>: [{}]'.format(' '.join('{0:08b}'.format(byte) for byte in ba)))
        self._write_fn(ba)
