Low level IC drivers for use with Python directly.

All devices require instantiated interfaces and only read/write functions passed into constructors. See tests for usage examples.

Interface opening and closing is left to the caller.

Implementations usually are not complete, only as much as I have needed and had a chance to test.

Most of the devices have been tested using FT232H or Raspberry Pi, usually mentioned in code comment.

Device tree is split by interface used on the IC:
* I2C
    * PAC193x power meter
    * SHT3x temperature/humidity sensor
    * AD7156 2 channel CDC (Capacitance to digital converter)
    * AD7147 13 channel CapTouch Programmable Controller for Single-Electrode Capacitance Sensors
* SPI
    * AD5689R dual channel 16-bit DAC with internal 2.5V reference
* UART
