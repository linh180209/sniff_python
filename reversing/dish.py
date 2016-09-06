import sys
sys.path.append("..")
import random
import math
import time
from fuzzing import cangendata
from CanLib.CAN_Packet import *
from CanLib.CAN_Driver import *

#This function is to dish system via can frames
#Example: 
# sudo python dish.py /dev/ttyACM0 0x266 0 8 0.01 local
# or
# sudo python3.4 dish.py vcan0 0x266 0 8 0.01 local

def analyzebyte(dev,canid,indicate1=0,indicate2=8, delay=0.01,cloudflag="local"):

	startbase = "0x80"
	top = "0xFF"
	bottom = "0x0"
	direction = "up"
	loopflag = 1
		
	while startbase != top or startbase != bottom:		
		#regular(dev,canid,indicate1=0,indicate2=8,startbase=0x80, topcount=0xFF, lowcount=0x0,direction="up",cloudflag="local",delay=0.01)
		cangendata.regular(dev,canid,indicate1,indicate2,startbase,top,bottom,direction,cloudflag, delay)
		
		
		dishdirection = raw_input("\nRepeat or Reverse Direction or nothing?(y,r or n): \r\n")
		if dishdirection == "r":
			if direction == "up":
				direction = "down"			
			else:
				direction = "up"
		elif dishdirection == "n":
			if direction == "up":
				bottom = startbase
				startbase = str(hex((int(startbase,16)+int(top,16))/2))
			else:
				top = startbase
				startbase = str(hex((int(startbase,16)+int(bottom,16))/2 ))
			
			dishdirection = raw_input("\ngo deeply, up or down?(u or d): \r\n")
				
			if dishdirection == "u":
				direction = "up"		
			else:
				direction = "down"

	return startbase

if __name__ == "__main__":

	print ("Usage: python dish.py <candev> <can ID> <byterange1> <byterange2> <delay time> <testing mode>")
	print ("or")
	print ("Usage: python3.4 dish.py <candev> <can ID> <byterange1> <byterange2> <delay time> <testing mode>")

	if(sys.version_info >= (3,3)):
		dev = CANDriver(TypeCan.SOCKET,name_dev=sys.argv[1])
	else:
		dev = CANDriver(TypeCan.SERIAL,port=sys.argv[1],bit_rate=125000)
	dev.operate(Operate.START)
	analyzebyte(dev,sys.argv[2],int(sys.argv[3]),int(sys.argv[4]), float(sys.argv[5]),"local")	

	print ("Finish dish!")
