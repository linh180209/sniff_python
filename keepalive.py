import sys
from CanLib.CAN_Packet import *
from CanLib.CAN_Driver import *
from CanLib.CAN_protocol import *
import time
import multiprocessing

# This function is to send tester present data to make testing device awake
# sudo python keepalive.py /dev/ttyACM0 0x7df 125000
# or
# sudo python3.4 keepalive.py vcan0 0x7df
# Payloads: 0x7df(Request ID)

def feedstart(devq,udsentry = 0x7df):   #devq is object of can queue 
	
	try:
		if udsentry.startswith("0x"):
			canid = int(udsentry, base=16)
		else:
			canid = int(udsentry)
	except (AttributeError, ValueError):
		raise ValueError('error canid')


	keeptask = multiprocessing.Process(target=feedtask,args=(canid,))
	keeptask.start()
	
	return keeptask


def feedtask(canid):   #devq is object of can queue 

	data = [0x02, 0x3E, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00]
	fr = CAN_Packet()
	fr.configure(canid,0x8,data)
	
	while True:
		devq.send_packet(fr)
		time.sleep(1)

def feedstop(task=None):
	task.terminate()


if __name__ == "__main__":
	
	print ("Usage: sudo python keeplive.py <candev> <request_id> <baudrate>")
	print ("or")
	print ("Usage: sudo python3.4 keeplive.py <candev> <request_id>")

	#check payloads
	if (len(sys.argv) < 3):
		print ('You must specify one can device and Request ID')
		exit(1)
	if(sys.version_info >= (3,3)):
		dev = CANDriver(TypeCan.SOCKET,name_dev=sys.argv[1])
	else:
		dev = CANDriver(TypeCan.SERIAL,port=sys.argv[1],bit_rate=int(sys.argv[3]))
	devq = ISOTP_driver(dev)
	devq.operate(Operate.START)
		

	taskname = feedstart(devq,sys.argv[2])
	print ("Keep alive produce is running")

	while True:
		c = raw_input("Still sending frames to the bus, stop the process? (y or n)")
		if(c == 'y'):
			feedstop(taskname)
			devq.operate(Operate.STOP)
			print ('========EXIT========')
			exit()
	
		

	
