import sys
sys.path.append("..")
import random
import math
import time
import cangendata
from CanLib.CAN_Packet import * 
from CanLib.CAN_Driver import *

#This function is to Generate random fuzzing can frames(include id and data). 
#Example: 
# sudo python fuzzran.py /dev/ttyACM0 0 8 100 0.01


if __name__ == "__main__":

	dev = CANDriver(TypeCan.SERIAL,port=sys.argv[1],bit_rate=125000)
	dev.operate(Operate.START)
	print "Benson mark Usage: python fuzzran.py <candev> <byterange1> <byterange2> <framecount> <delay time>"

	
	for i in range (0,int(sys.argv[4])):
		canid = random.randint(0,2047)
		cangendata.fixedlen(dev,str(canid),int(sys.argv[2]),int(sys.argv[3]),1,float(sys.argv[5]))
		#dev.sendframesfromfile(dev,'fuzzran.json')
