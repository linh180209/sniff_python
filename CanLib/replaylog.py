import os
import sys
sys.path.append("..")
from CanLib.CAN_Driver import *
from CanLib.vtlog import *
from CanLib.CAN_Packet import *

#This function is to replay can frame log(jason format). 
#Example: 
# sudo python replaylog.py /dev/ttyACM0 log1.json 125000 1b1
# or
# sudo python3.4 replaylog.py vcan0 log1.json 1b1
# payloads: log1.json(log file name),125000(baudrate), 1b1(replay log one by one flag)
#Author: BensonYang
#Date: 26072016


def start(self,dev,filename = None,replayflag = "", delay=0.01):  #no need this function, we can put sys argv as input doscount = 1000, time = 0, delay=0.1
	

	data = [0 for x in range(8)]
	FILEPATH = os.getcwd()
	filename = FILEPATH + '/logfolder/'+ filename
	if replayflag == "1b1":
		dev.sendframesfromfile1b1(dev,filename)
	else:
		dev.sendframesfromfile(dev,filename)


if __name__ == "__main__":
	
	print ("Usage: sudo python replaylog.py candev filename baudrate")	

	if (len(sys.argv) < 2):
		print ('You must specify one can device')
		exit(1)
	else:
		name_devices = sys.argv[1]
	
	if(sys.version_info >= (3,3)):
		dev = CANDriver(TypeCan.SOCKET,name_dev=sys.argv[1])
		dev.operate(Operate.START)
		if(sys.argv[2][-4:] == "json"):	# send frames from log file  

			if(len(sys.argv) > 3):
				start(None,dev,sys.argv[2],sys.argv[3])
			else:
				start(None,dev,sys.argv[2])
		else:
			print ("file format is incorrect")

	else:
		dev = CANDriver(TypeCan.SERIAL,port=sys.argv[1],bit_rate=int(sys.argv[3]))
		dev.operate(Operate.START)
		if(sys.argv[2][-4:] == "json"):	# send frames from log file  

			if(len(sys.argv) > 4):
				start(None,dev,sys.argv[2],sys.argv[4])
			else:
				start(None,dev,sys.argv[2])
		else:
			print ("file format is incorrect")

	
	
	
	
	


	
