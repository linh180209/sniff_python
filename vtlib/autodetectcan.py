import sys
sys.path.append("..")
from vtlib import can
from vtlib.hw import vtbox
from vtlib.utils.queue import CanQueue
import time

# This function is to detect can frames and set baudrate automatically
# sudo python autodetectcan.py /dev/ttyACM0

def detect_can(can_dev):  # dev is object of vtbox dev 

	dev = vtbox.vtboxDev(can_dev)
	devq = CanQueue(dev)
	devq.start()

	i = 4
	j = 0
	loop =0
	detected = 0
	data = [0 for x in range(8)]
	fr = can.Frame(0x00,8,data)  #can id

	baudset = 'S'+str(i)+'\r'

	while True:
		dev.stop()
		dev.ser.write(baudset)
		dev.start()
		if i in [4,6]:
			loop = 4
		else:
			loop = 2
		for j in range(0,loop):
			devq.send(fr)
			try:
				recvfr,frflag = devq.recv(timeout=0.5, filter=None)
				if recvfr:
					print "Detected CAN Bus baudrate successfully!"

					if baudset == 'S0\r':
						baudrate = 10000
					elif baudset == 'S1\r':
						baudrate = 20000
					elif baudset == 'S2\r':
						baudrate = 50000
					elif baudset == 'S3\r':
						baudrate = 100000
					elif baudset == 'S4\r':
						baudrate = 125000
					elif baudset == 'S5\r':
						baudrate = 250000
					elif baudset == 'S6\r':
						baudrate = 500000
					elif baudset == 'S7\r':
						baudrate = 750000
					elif baudset == 'S8\r':
						baudrate = 1000000
					else:
					    raise ValueError("baudrate not supported")

					print baudrate 
					
					detected = 1
			except:
				pass

		i +=1		
		
		if i > 8:
			print "No CAN message detected!"
			i = 0	

		if detected:
			dev.stop()
			return baudrate

		baudset = 'S'+str(i)+'\r'
		print baudset
		


if __name__ == "__main__":

	detect_can(sys.argv[1])
	exit()
	
    
    
