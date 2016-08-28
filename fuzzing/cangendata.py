import sys
sys.path.append("..")
import random
import math
import time
from vtlib.utils import autodetectcan
from vtlib import can 
from vtlib.hw import vtbox
from vtlib import vtlog
from vtlib.proto.isotp import IsoTpProtocol, IsoTpMessage


#This function is to Generate can frames. One is fixed length of can data. The other one is random. 
#example : 
# fixed length:  sudo python cangendata.py /dev/ttyACM0 0x266 0 8 100 0.01 local  Payloads: 0x266(CAN ID),0(Indicator1),8(Indicator2),100(Can frame count),0.01(delay time)
# random length: sudo python cangendata.py /dev/ttyACM0 0x266 long 100 0.01 local Payloads: 0x266(CAN ID),long(flag for long length data),100(Can frame count),0.01(delay time)
# Regular data with fixed length: sudo python cangendata.py /dev/ttyACM0 0x266 regular 0 8 0x80 0xFF 0x0 0.01 up[down] local
# payload:0x266(CAN ID),regular(flag for regular data),0(Indicator1),8(Indicator2),0x80(start number from 0x00~0xFF),0xFF(TOP number from 0x00~0xFF),0x0(LOW number from 0x00~0xFF),0.01(delay time),up(direction:up for increasing, down for decreasing)
#Author: BensonYang
#Date: 26072016

def fixedlen(dev,canid,indicate1=0,indicate2=8,framecount = 1000, delay=0.01,cloudflag="local"):  #fixed len of can frame to 8 bytes
	
	# parse canid
	try:

		if canid.startswith("0x"):
			canidint = int(canid, base=16)
		else:
			canidint = int(canid)

	except (AttributeError, ValueError):
		raise ValueError('error canid')

	VTlogfile = vtlog.VTlog()
	frbuffer = []	

	for n in range(0,framecount):
		data = [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
		for i in range(indicate1,indicate2):
				seed = random.randint(0,255)
				data[i] = seed
		vtmsg = vtlog.VTMessage(canidint,8,data,1,delay,"S")
		frbuffer.append(vtmsg)
		if cloudflag == "local":
			fr = can.Frame(canidint,8,data,1)
			dev.send(fr)
			print fr
	filename = VTlogfile.writelog(frbuffer)
	return filename

def flexlen(dev,canid,framecount = 1000, delay=0.01,cloudflag="local"):   #len of can frame changes from 0 to 255

	# parse canid
	try:

		if canid.startswith("0x"):
			canidint = int(canid, base=16)
		else:
			canidint = int(canid)
	except (AttributeError, ValueError):
		raise ValueError('error canid')

	VTlogfile = vtlog.VTlog()
	frbuffer = []	

	isop = IsoTpProtocol()
	isom = IsoTpMessage(canidint)

	for n in range(0,framecount):

		isom.length = random.randint(0,255)
		isom.data = []
		for i in range(0,isom.length):
			isom.data.append(random.randint(0,255))

	
		for fr in isop.generate_frames(isom):
			vtmsg = vtlog.VTMessage(canidint,8,fr.data,1,delay,"S")
			frbuffer.append(vtmsg)
			if cloudflag == "local":
				#fr = can.Frame(canidint,8,data,1)
				print fr
				dev.send(fr)	

	filename = VTlogfile.writelog(frbuffer)
	return filename

def regular(dev,canid,indicate1=0,indicate2=8,startbase=0x80, topcount=0xFF, lowcount=0x0,direction="up",cloudflag="local",delay=0.01):
	# parse canid
	try:

		if canid.startswith("0x"):
			canidint = int(canid, base=16)
		else:
			canidint = int(canid)

	except (AttributeError, ValueError):
		raise ValueError('error canid')

	# parse startbase
	try:

		if startbase.startswith("0x"):
			datacount = int(startbase, base=16)
		else:
			datacount = int(startbase)

	except (AttributeError, ValueError):
		raise ValueError('error start count number')

	try:

		if startbase.startswith("0x"):
			datatop = int(topcount, base=16)
		else:
			datatop = int(topcount)

	except (AttributeError, ValueError):
		raise ValueError('error top count number')

	try:

		if startbase.startswith("0x"):
			datalow = int(lowcount, base=16)
		else:
			datalow = int(lowcount)

	except (AttributeError, ValueError):
		raise ValueError('error low count number')
	
	#print datacount,datatop,datalow

	VTlogfile = vtlog.VTlog()
	frbuffer = []

	if direction == "up":
		while datacount <= datatop:
			data = [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
			for i in range(indicate1,indicate2):
					data[i] = datacount
			datacount += 1
			vtmsg = vtlog.VTMessage(canidint,8,data,1,delay,"S")
			frbuffer.append(vtmsg)
			if cloudflag == "local":
				fr = can.Frame(canidint,8,data,1)
				dev.send(fr)
				print fr
	else:
		while datacount >= datalow:
			data = [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
			for i in range(indicate1,indicate2):
					data[i] = datacount
			datacount -= 1
			vtmsg = vtlog.VTMessage(canidint,8,data,1,delay,"S")
			frbuffer.append(vtmsg)
			if cloudflag == "local":
				fr = can.Frame(canidint,8,data,1)
				dev.send(fr)
				print fr

	filename = VTlogfile.writelog(frbuffer)
	return filename

	

if __name__ == "__main__":


	dev = vtbox.vtboxDev(sys.argv[1],125000)

	print "Benson mark Usage: python cangendata.py <candev> <can_id> <byterange1> <byterange2> [longlengthflag/regularflag] <frame count> <delay time>"
	print "Generating Frames..."

	if sys.argv[3]=="long":		#already input long lengthflag
		flexlen(dev,sys.argv[2],int(sys.argv[4]),float(sys.argv[5]),sys.argv[6])
		#dev.sendframesfromfile(dev,'cangendata.json')
	elif sys.argv[3]=="regular":
		#sudo python cangendata.py /dev/ttyACM0 0x266 regular 0 8 0x80 0xFF 0x0 0.01 up[down] local
		#regular(dev,canid,indicate1=0,indicate2=8,startbase=0x80, topcount=0xFF, lowcount=0x0,direction="up",cloudflag="local",delay=0.01)
		filename = regular(dev,sys.argv[2],int(sys.argv[4]),int(sys.argv[5]),sys.argv[6],sys.argv[7],sys.argv[8],sys.argv[10],sys.argv[11],sys.argv[9])
		#dev.sendframesfromfile(dev,filename)
		
	else:	
		filename = fixedlen(dev,sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]),float(sys.argv[6]),sys.argv[7])
		dev.sendframesfromfile(dev,filename)

