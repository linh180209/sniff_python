import sys
sys.path.append("..")
from CanLib.CAN_Packet import *
from CanLib.CAN_Driver import *
from CanLib.CAN_protocol import *
import time

# This function is to test the capability of message handling rate
# example: sudo python mhrtest.py /dev/ttyACM2 125000 100 0.05 0x7df 0x7ac
# or
# sudo python3.4 mhrtest.py vcan0 100 0.05 0x7df 0x7ac
# payloads: 125000(baud rate), 100(can frame count), 0.01(time delay), 0x7df(request ID),0x7ac(Service ID)
#Author: BensonYang
#Date: 26072016

def test(devq,framecount,delay,udsentry = 0x7df,sid = 0x01):   #devq is object of can queue 
	print ("delay: %f"%delay)
	mhr = 0.0
	respcount = 0.0
	data = [0x02, 0x3E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
	fr = CAN_Packet()
	fr.configure(udsentry,0x8,data)

	for loop in range(0,framecount):  
		devq.send_packet(fr)
		
		print (loop,fr)
		time.sleep(delay)
		recvfr,flag = devq.get_packet(timeout=delay, filter=sid)
		if recvfr != None:
			print (recvfr)
			respcount += 1
	
	mhr = respcount/framecount
	print ("mhr: %f"%mhr)

	return mhr

def test_delay(devq,framecount,delay,udsentry = 0x7df,sid = 0x01):
	while(test(devq,framecount,delay,udsentry,sid) < 1):
		delay += 0.01
	return delay
	

if __name__ == "__main__":
	
	print ("Usage: sudo python dosflood.py <candev> <baudrate> <canframe count> <time delay> <DEST ID> <SID>")
	print ("or")
	print ("Usage: sudo python3.4 dosflood.py <candev> <canframe count> <time delay> <DEST ID> <SID>\n")	
	if(sys.version_info >= (3,3)):
		dev = CANDriver(TypeCan.SOCKET,name_dev=sys.argv[1])
		devq = ISOTP_driver(dev)
		devq.operate(Operate.START)

		try:

			if sys.argv[4].startswith("0x") and sys.argv[5].startswith("0x"):
				destid = int(sys.argv[4], base=16)
				sid = int(sys.argv[5], base=16)
			else:
				destid = int(sys.argv[4])
				sid = int(sys.argv[5])
		except (AttributeError, ValueError):
			raise ValueError('error canid')
		print ('sid: 0x%X'%sid)
		print ("The program is runing!")
	
		hdelay = test_delay(devq,int(sys.argv[2]),float(sys.argv[3]),destid,sid)	

		print ("Message Handling Delay(s):")
		print (hdelay)
		exit()
	else:
		dev = CANDriver(TypeCan.SERIAL,port=sys.argv[1],bit_rate=125000)
		devq = ISOTP_driver(dev)
		devq.operate(Operate.START)

		try:

			if sys.argv[5].startswith("0x") and sys.argv[6].startswith("0x"):
				destid = int(sys.argv[5], base=16)
				sid = int(sys.argv[6], base=16)
			else:
				destid = int(sys.argv[5])
				sid = int(sys.argv[6])
		except (AttributeError, ValueError):
			raise ValueError('error canid')
		print ('sid: 0x%X'%sid)
		print ("The program is runing!")
	
		hdelay = test_delay(devq,int(sys.argv[3]),float(sys.argv[4]),destid,sid)	

		print ("Message Handling Delay(s):")
		print (hdelay)
		exit()
