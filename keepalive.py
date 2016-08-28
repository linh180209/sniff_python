import sys
from vtlib import can
from vtlib.hw import vtbox
from vtlib.utils.queue import CanQueue
import time
import multiprocessing

# This function is to send tester present data to make testing device awake
# sudo python keepalive.py /dev/ttyACM0 0x7df 125000
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
	fr = can.Frame(canid)  #can id
	fr.dlc = 0x8           #data length
	fr.data = data
	
	while True:
		devq.send(fr)
		time.sleep(1)

def feedstop(task=None):
	task.terminate()


if __name__ == "__main__":
	
	print "Usage: sudo python keeplive.py <candev> <request_id> <baudrate>"

	#check payloads
	if (len(sys.argv) < 3):
		print 'You must specify one can device and Request ID'
		exit(1)

	dev = vtbox.vtboxDev(sys.argv[1],int(sys.argv[3]))
	devq = CanQueue(dev)
	devq.start()
		

	taskname = feedstart(devq,sys.argv[2])
	print "Keep alive produce is running"

	while True:
		c = raw_input("Still sending frames to the bus, stop the process? (y or n)")
		if(c == 'y'):
			feedstop(taskname)
			print '========EXIT========'
			exit()
	
		

	
