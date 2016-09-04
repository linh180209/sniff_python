from CanLib.CAN_Packet import *
from CanLib.CAN_Driver import *
from CanLib.CAN_protocol import *
import time
import sys
from CanLib.autodetectcan import *

# This function is to check the status of testing device. The function will return True if the testing device is alive. Othervise, return false
# sudo python tdstatus.py /dev/ttyACM0 125000
#Author: BensonYang
#Date: 26072016

def check(devq,udsentry = 0x7df):   #devq is object of can queue 

	statusflag = 0	

	data = [0x02, 0x3E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
	fr = CAN_Packet()
	fr.configure(udsentry,0x8,data)


	for loog in range(0,4):  #try 3 times
		try:
			recvfr,flag = devq.get_packet(timeout=1, filter=None)
			if recvfr != None:
				statusflag = 1
			else:
				devq.send_packet(fr)
				devq.send_packet(fr)
				recvfr,flag = devq.get_packet(timeout=1, filter=None)
				if recvfr != None:
					statusflag = 1			
		except:
			pass
	return statusflag

def recover(devq,udsentry = 0x7df):  #recover the sys to default section
	
	data = [0x02, 0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]
	fr = CAN_Packet()
	fr.configure(udsentry,0x8,data)

	devq.send_packet(fr)
	devq.send_packet(fr)
	
	try:
		recvfr,flag = devq.get_packet(timeout=1, filter=None)
		if recvfr != None:
			return True
		else:
			return False
	except:
		pass

if __name__ == "__main__":
	

	dev = CANDriver(sys.argv[1],int(sys.argv[2]))
	#autodetectcan.detect_can(dev)
	devq = ISOTP_driver(dev)
	devq.operate(Operate.START)
	
	print "Checking the status of device:"

	if check(devq,0x7df):
		print "Testing device is alive"
	else:
		recover(devq,0x7df)
		if check(devq,0x7df):
			print "Testing device is alive"
		else:
			print "Cannot Get any Info from Testing Device! Please check the cable or testing device working status manually"
