import sys
sys.path.append("..")
import random
import math
import time
from CanLib.CAN_Packet import *
from CanLib.CAN_Driver import *
from CanLib.vtlog import *

#This function is to analyze the affection when setting different bits of can frame 
#Example: 
# sudo python dish.py /dev/ttyACM0 0x266 0 1 0.01 local 125000
# or
# sudo python3.4 dish.py vcan0 0x266 0 1 0.01 local
# payloads meaning: 0x266(can id), 0 1(data indicator) 0.01(time gap between frames) local(run in local) 125000(can bus baudrate)

def SET_BIT(self, val, bitIndex):
	val_0 = 1 << bitIndex
	val = val | val_0
	return val

def CLEAR_BIT(self,val, bitIndex):
	val_0 = ~(1 << bitIndex)
	val = val & val_0
	return val

def IS_SET(self, val, bitIndex): #to confirm if realated is set to 1 properly. If not, return 0. Otherwise, return 1.
	val_0 = 1 << bitIndex
	val = val & val_0
	return val

def analyzebit(dev,canid,indicate1=0,indicate2=8, delay=0.01,cloudflag="local"):

	# parse canid
	
	try:

		if canid.startswith("0x"):
			canidint = int(canid, base=16)
		else:
			canidint = int(canid)

	except (AttributeError, ValueError):
		raise ValueError('error canid')


	VTlogfile = VTlog()
	frbuffer = []
	data = [0 for x in range(8)]
	startbase = 0
	exitbitana = 0
		
	for i in range(1,8):
		if exitbitana:
			break
		startbase = (startbase << 1) + 1
		bytedata = startbase
		for j in range(0,(8-i)):

			bytedata = bytedata << 1
			for n in range(indicate1,indicate2):
				data[n] = bytedata
					
			print (bin(bytedata))
			print (data)			
			if cloudflag == "local":
				loop = 1
				while(loop):
					fr = CAN_Packet()
					fr.configure(canidint,8,data,1)
					dev.send_driver(fr)
					dev.send_driver(fr)
					dev.send_driver(fr)
					print (fr)
					bitcomment = raw_input("\nrepeat?(y or n): \r\n")
					if bitcomment == "n":
						loop = 0
			bitcomment = raw_input("\nimport bit? if yes, please comment the affection. if no, press Enter directly: \r\n")
				
			if bitcomment != "":
				vtmsg = VTMessage(canidint,8,data,5,delay,"S")
				frbuffer.append(vtmsg)
				frbuffer[-1]= VTMessage(fr.id,8,fr.get_payload(),5,0.01,"S",bitcomment)

			c = raw_input("\nfinish the process?(y or n): \r\n")

			if c == "y":
				exitbitana = 1
				break
				
			
	logname = VTlogfile.writelog(frbuffer)
	print (logname)
	return logname

if __name__ == "__main__":

	print ("Usage: python bit.py <candev> <can ID> <byterange1> <byterange2> <delay time> <testing mode> <baudrate>")
	print ("or")
	print ("Usage: python3.4 bit.py <candev> <can ID> <byterange1> <byterange2> <delay time> <testing mode>")
	if(sys.version_info >= (3,3)):
		dev = CANDriver(TypeCan.SOCKET,name_dev=sys.argv[1])
	else:
		dev = CANDriver(TypeCan.SERIAL,port=sys.argv[1],bit_rate=125000)
	dev.operate(Operate.START)

	analyzebit(dev,sys.argv[2],int(sys.argv[3]),int(sys.argv[4]), float(sys.argv[5]),"local")	

	print ("Finish bit analyze!")
