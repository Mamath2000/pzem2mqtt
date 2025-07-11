from modbus_tk import modbus_rtu
import modbus_tk.defines as cst
import serial

# serial_port = "/dev/ttyUSB0"  # adapte si nécessaire
serial_port = "/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0"

ser = serial.Serial(port=serial_port, baudrate=9600, bytesize=8, parity='N', stopbits=1)
master = modbus_rtu.RtuMaster(ser)
master.set_timeout(3.0)
master.set_verbose(True)

data = master.execute(1, cst.READ_INPUT_REGISTERS, 0, 10)
print("Data:", data)