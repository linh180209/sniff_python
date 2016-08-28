import os
import sys
import time
sys.path.append("..")
from vtlib.hw.vtbox import vtboxDev
from vtlib import vtlog
from vtlib.utils.queue import CanQueue
from vtlib import can

#This function is to log can frames to file(jason format). 
#Example: 
# sudo python logdata.py /dev/ttyACM0 125000 10
# payloads:125000(baudrate), 10(10 seconds)
#Author: BensonYang
#Date: 15082016


def start(self,dev,logtime=5):  #no need this function, we can put sys argv as input doscount = 1000, time = 0, delay=0.1
	
	logdataobj = []

	devq = CanQueue(dev)
	devq.start()
	VTlogfile = vtlog.VTlog()	
	start_time = time.time()
	print "Start Logging data..."

	#while in 2 min and not press 'q' to exit
	while((time.time()-start_time) < logtime):		
		frame = None
		while(frame == None):
			frame,frameflag =  devq.recv(1,None)	
		logdataobj.append(frame)	

	logname = VTlogfile.logfrarray2file(VTlogfile,logdataobj,"P","Log Frames")
	devq.stop()
	
	print "Finish logging!"
	print logname

	return logname



if __name__ == "__main__":
	
	print "Usage: sudo python logdata.py candev baudrate logtime"	

	if (len(sys.argv) < 2):
		print 'You must specify one can device'
		exit(1)
	else:
		name_devices = sys.argv[1]

	dev = vtboxDev(sys.argv[1],int(sys.argv[2]))
	
	
	start(None,dev,int(sys.argv[3]))

	
	
	
	


	
