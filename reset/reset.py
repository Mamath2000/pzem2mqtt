#!/usr/bin/python3

import pymodbus
import serial
import math
import time

from pymodbus.pdu import ModbusRequest
from pymodbus.client import ModbusSerialClient as ModbusClient
#from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.transaction import ModbusRtuFramer


def calc (registers, factor):
    format = '%%0.%df' % int (math.ceil (math.log10 (factor)))
    if len(registers) == 1:
        return format % ((1.0 * registers[0]) / factor)
    elif len(registers) == 2:
        return format % (((1.0 * registers[1] * 65535) + (1.0 * registers[0])) / factor)


client = ModbusClient (method = "rtu", port="/dev/ttyUSB0", stopbits = 1, bytesize = 8, parity = 'N', baudrate = 9600)

#Connect to the serial modbus server
connection = client.connect()
if client.connect ():
        try:
            # Reset energy count
            # 0x01 Slave address
            # 0x42 Magic code
            # 0x80 CRC for slave address (0x01)
            # 0x11 CRC for magic code (0x42)

            print ("======= address 0x01 =====")
            data = [0x01, 0x42, 0x80, 0x11]
            print(client.send(data))
            time.sleep(2)
            result = client.read_input_registers (0x0000, 10, unit = 0x01)
            print(result.registers)
            print (calc (result.registers[5:7], 1) + 'Wh')

            print ("======= address 0x02 =====")
            data = [0x02, 0x42, 0x80, 0xE1]
            print(client.send(data))
            time.sleep(2)
            result = client.read_input_registers (0x0000, 10, unit = 0x02)
            print(result.registers)
            print (calc (result.registers[5:7], 1) + 'Wh')

            print ("======= address 0x03 =====")
            data = [0x03, 0x42, 0x81, 0x71]
            print(client.send(data))
            time.sleep(2)
            result = client.read_input_registers (0x0000, 10, unit = 0x03)
            print(result.registers)
            print (calc (result.registers[5:7], 1) + 'Wh')

            print ("======= address 0x04 =====")
            data = [0x04, 0x42, 0x83, 0x41]
            print(client.send(data))
            time.sleep(2)
            result = client.read_input_registers (0x0000, 10, unit = 0x04)
            print(result.registers)
            print (calc (result.registers[5:7], 1) + 'Wh')


        finally:
            client.close()
