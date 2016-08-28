import os
import sys
sys.path.append("..")
from vtlib.hw.vtbox import vtboxDev
from vtlib import vtlog
from vtlib import can

#This function is to replay can frame log(jason format). 
#Example: 
# sudo python replaylog.py /dev/ttyACM0 log1.json 125000 1b1
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
	
	print "Usage: sudo python replaylog.py candev filename baudrate"	

	if (len(sys.argv) < 2):
		print 'You must specify one can device'
		exit(1)
	else:
		name_devices = sys.argv[1]

	dev = vtboxDev(sys.argv[1],int(sys.argv[3]))
	
	if(sys.argv[2][-4:] == "json"):	# send frames from log file  

		if(len(sys.argv) > 4):
			start(None,dev,sys.argv[2],sys.argv[4])
		else:
			start(None,dev,sys.argv[2])
	else:
		print "file format is incorrect"

	
	
	
	
	


	