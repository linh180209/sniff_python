import os
import sys
import time
sys.path.append("..")
from CanLib.CAN_Driver import *
from CanLib.vtlog import *
from CanLib.CAN_protocol import *
from CanLib.CAN_Packet import *

#This function is to log can frames to file(jason format). 
#Example: 
# sudo python logdata.py /dev/ttyACM0 125000 10
# or
# sudo python3.4 logdata.py vcan0 10
# payloads:125000(baudrate), 10(10 seconds)
#Author: BensonYang
#Date: 15082016


def start(self,dev,logtime=5):  #no need this function, we can put sys argv as input doscount = 1000, time = 0, delay=0.1
	
	logdataobj = []
	
	#devq = CanQueue(dev)
	devq = ISOTP_driver(dev)
	devq.operate(Operate.START)
	VTlogfile = VTlog()	
	start_time = time.time()
	print ("Start Logging data...")

	#while in 2 min and not press 'q' to exit
	while((time.time()-start_time) < logtime):		
		packet = None
		while(packet == None):
			packet,flag =  devq.get_packet()
			print (packet)	
		logdataobj.append(packet)	
	logname = VTlogfile.logfrarray2file(VTlogfile,logdataobj,"P","Log Frames")
	devq.operate(Operate.STOP)
	
	print ("Finish logging!")
	print (logname)

	return logname



if __name__ == "__main__":
	
	print ("Usage: sudo python logdata.py candev baudrate logtime")
	print ("or")
	print ("Usage: sudo python3.4 logdata.py candev logtime")		

	if (len(sys.argv) < 2):
		print ('You must specify one can device')
		exit(1)
	else:
		name_devices = sys.argv[1]
	if(sys.version_info >= (3,3)):
		dev = CANDriver(TypeCan.SOCKET,name_dev=sys.argv[1])
		start(None,dev,int(sys.argv[2]))
	else:
		dev = CANDriver(TypeCan.SERIAL,port=sys.argv[1],bit_rate=int(sys.argv[2]))
		start(None,dev,int(sys.argv[3]))
	
	

	
	
	
	


	
