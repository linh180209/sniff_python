import sys
sys.path.append("..")
from vtlib import can
from vtlib.hw import vtbox
from vtlib.utils.queue import CanQueue
import time

# This function is to test the capability of message handling rate
# example: sudo python mhrtest.py /dev/ttyACM2 125000 100 0.05 0x7df 0x7ac
# payloads: 125000(baud rate), 100(can frame count), 0.05(time delay), 0x7df(request ID),0x7ac(Service ID)
#Author: BensonYang
#Date: 26072016

def test(devq,framecount,delay,udsentry = 0x7df,sid = 0x01):   #devq is object of can queue 

	mhr = 0.0
	respcount = 0.0
	data = [0x02, 0x3E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
	fr = can.Frame(udsentry)  #can id
	fr.dlc = 0x8           #data length
	fr.data = data


	for loop in range(0,framecount):  
		devq.send(fr)
		
		print loop,fr
		time.sleep(delay)

		recvfr,frflag = devq.recv(timeout=delay, filter=sid)
		if recvfr != None:
			print recvfr
			respcount += 1
	
	mhr = respcount/framecount

	return mhr



if __name__ == "__main__":
	
	print "Usage: sudo python dosflood.py <candev> <baudrate> <canframe count> <time delay> <DEST ID> <SID>\n"	

	dev = vtbox.vtboxDev(sys.argv[1],125000)
	devq = CanQueue(dev)
	devq.start()

	try:

		if sys.argv[5].startswith("0x") and sys.argv[6].startswith("0x"):
			destid = int(sys.argv[5], base=16)
			sid = int(sys.argv[6], base=16)
		else:
			destid = int(sys.argv[5])
			sid = int(sys.argv[6])
	except (AttributeError, ValueError):
		raise ValueError('error canid')

	print "The program is runing!"
	
	hrate = test(devq,int(sys.argv[3]),float(sys.argv[4]),destid,sid)	

	print "Message Handling Rate:"
	print hrate
	exit()
