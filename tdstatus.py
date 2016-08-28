from vtlib import can
from vtlib.hw import vtbox
from vtlib.utils.queue import CanQueue
import time
import sys
from vtlib import autodetectcan

# This function is to check the status of testing device. The function will return True if the testing device is alive. Othervise, return false
# sudo python tdstatus.py /dev/ttyACM0 125000
#Author: BensonYang
#Date: 26072016

def check(devq,udsentry = 0x7df):   #devq is object of can queue 

	statusflag = 0	

	data = [0x02, 0x3E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
	fr = can.Frame(udsentry)  #can id
	fr.dlc = 0x8           #data length
	fr.data = data


	for loog in range(0,4):  #try 3 times
		try:
			recvfr,recvflag = devq.recv(timeout=1, filter=None)
			if recvfr != None:
				statusflag = 1
			else:
				devq.send(fr)
				devq.send(fr)
				recvfr,recvflag = devq.recv(timeout=1, filter=None)
				if recvfr != None:
					statusflag = 1			
		except:
			pass
	return statusflag

def recover(devq,udsentry = 0x7df):  #recover the sys to default section
	
	data = [0x02, 0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]
	fr = can.Frame(udsentry)  #can id
	fr.dlc = 0x8           #data length
	fr.data = data

	devq.send(fr)
	devq.send(fr)
	
	try:
		recvfr,recvflag = devq.recv(timeout=1, filter=None)
		if recvfr != None:
			return True
		else:
			return False
	except:
		pass

if __name__ == "__main__":
	

	dev = vtbox.vtboxDev(sys.argv[1],int(sys.argv[2]))
	#autodetectcan.detect_can(dev)
	devq = CanQueue(dev)
	devq.start()
	
	print "Checking the status of device:"

	if check(devq,0x7df):
		print "Testing device is alive"
	else:
		recover(devq,0x7df)
		if check(devq,0x7df):
			print "Testing device is alive"
		else:
			print "Cannot Get any Info from Testing Device! Please check the cable or testing device working status manually"
