Python interface drivers for I2C devices.

All the device drivers expect bus (de)initialization done on caller side. Only functions are expected to be passed in for read and write. Examples based on pyftdi can be seen in 'tests' directory.

* PAC193x: Microchip DC Power/Energy meter with accumulator

* SHT3x: Sensirion temperature/humidity sensor

* AD7156: Analog devices 2 channel capacitance converter (CDC)

* AD7147: Analog Devices 13 channel capacitive sensor interface IC
