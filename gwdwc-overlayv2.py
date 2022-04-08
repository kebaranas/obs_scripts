import asyncio, serial, time
from serial.tools import list_ports



ports = list_ports.comports()
for n in ports:
    print(n.manufacturer)
print(ports)

try:
    port = serial.Serial('COM254', 115200)
except serial.SerialException:
    print('Error connecting to port')
else:
    print('Connected!!!!!!!!!')

while 1:
    if (port.in_waiting > 0):
        try:
            text = port.readline()
            print('read')
        except:
            print('Error')
        else:
            print(text)
    else:
        print("none")
        time.sleep(1)

#print(port)
#port.close()
#try:
#    file.write('hello world')
#finally:
#    file.close()