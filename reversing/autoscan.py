import sys
sys.path.append("..")
from CanLib.CAN_Packet import *
from CanLib.CAN_Driver import *
from CanLib.vtlog import *
from sys import stdout
import random
import math
import time
import argparse
import os
from CanLib import autoindeep
from CanLib import autodetectcan
from CanLib import replaylog
import bit

# This program is to scan can data automatically and try to revease the data
# sudo python autoscan.py /dev/ttyACM0 0 8 125000

def collectAllID(dev,totalframecount=3000,filename=None): #receive frames from dev in realtime. Or analyze frames from filename.

#============Collecting All CAN ID================================

	print "\n============================================================="
        print("Starting Collecting All CAN ID:\n")

	found_ids = []	
	vtmsgbuffer = []
	VTlogfile = VTlog()
	
        for i in range(0,totalframecount):   #total number can frame 
		try:
			fr = dev.receive_driver()
			#print fr
		except: 
			pass
		if fr != None:
			if fr.id not in found_ids:
				print("Last ID: 0x%X; total found %d" % (fr.id,len(found_ids) + 1))
				vtmsg = VTMessage(fr.id,8,fr.get_payload(),1,0.01,"C","Collect ID From Bus")
				vtmsgbuffer.append(vtmsg)
	    			found_ids.append(fr.id)
	
	found_ids.sort()
	
	logname = VTlogfile.writelog(vtmsgbuffer)
 	print("\nlog file: %s" % (logname))
	return vtmsgbuffer,found_ids

#=====CAN IDs are stored in vtmsgbuffer===============


def reverse(dev,fridbuffer=[],fuzzframecount=200,byterange1=0,byterange2=8):

	
	print "\n\n============================================================="
	print("Starting Reversing system")

	data = [0 for x in range(8)]
	fuzzcomment = []
	vtmsgbuffer = []
	keyid = []
	VTlogfile = VTlog()

	#==========start fuzzing==================================

	for i in range(0,len(fridbuffer)):
		fr = CAN_Packet() 		
		for fuzzloop in range(0,fuzzframecount): #fuzz number of frame
			for j in range(byterange1,byterange2):
					seed = random.randint(0,255)
					data[j] = seed
			fr.configure(fridbuffer[i],8,data)
			dev.send_driver(fr)
			vtmsg = VTMessage(fr.id,8,fr.get_payload(),1,0.01,"S","")
			vtmsgbuffer.append(vtmsg)
			time.sleep(0.01)  #10ms/frame
		print i
		fuzzcomment = raw_input("\nCAN ID:0x%X Any affection(y or n)? if no, press Enter directly: \r\n" % (fr.id)) #if there're no affection, press Enter to continue the program directly
		if fuzzcomment == "y":
			vtmsgbuffer[-1]= VTMessage(fr.id,8,fr.get_payload(),1,0.01,"K",fuzzcomment)
			keyid.append(fr.id)

	logname = VTlogfile.writelog(vtmsgbuffer)
	print "\n\n============================================================="
	print("\nlog file: %s" % (logname))
	print "\n=============Finish Reversing!================================="
	print "\n==============================================================="
	
	return keyid		#return key id that user comment it

if __name__ == "__main__":

	
	print "Usage: python autoscan.py <candev> <byterange1> <byterange2> <baudrate>"

	frbuffer = []
	fridarray = []
	keyid = []
	keyinfo = [[] for y in range(2048)]
	#VTlogfile = vtlog.VTlog()
	#vtmsgbuffer = []

	#baudrate = autodetectcan.detect_can(sys.argv[1])
	
	dev = CANDriver(sys.argv[1],int(sys.argv[4]))
	dev.operate(Operate.START)	
	#dev.ser.write(baudrate)
	

	frbuffer,fridarray = collectAllID(dev,3000,None)
		
	keyid = reverse(dev,fridarray,200,int(sys.argv[2]),int(sys.argv[3]))

	for i in range(0,len(keyid)):
		print ("The %d key ID: 0x%X" % (i+1,keyid[i]))

	keyinfo = autoindeep.analyzebytes(dev,keyid)

	print keyinfo

	#test value
	#keyinfo = [[303, 1, 'warning light']]


	#for i in range(0,len(keyinfo)):		#use dish method to analyze
	#	data = [0 for x in range(8)]
	#	index = keyinfo[i][1]
	#	data[index]= dish.analyzebyte(dev,keyinfo[i][0],index-1,index, 0.01,"local")
	#	fuzzcomment = raw_input("\nplease comment the byte: \r\n")
	#	vtmsg = vtlog.VTMessage(i,8,data,1,0.01,"K",fuzzcomment)
	#	vtmsgbuffer.append(vtmsg)
	#VTlogfile.writelog(vtmsgbuffer)

	#bit method 
	for i in range(0,len(keyinfo)):		#use bit method to analyze
		index = keyinfo[i][1]
		keylongfile = bit.analyzebit(dev,str(keyinfo[i][0]),index-1,index,0.01,"local")

	

	#replay the key frames to confirm

	VTlf = VTlog()
	VTMessagearray = []
	
	VTMessagearray	= VTlf.parselog(keylongfile)

	for i in range(0,len(VTMessagearray)):
		frame = CAN_Packet()
		frame.configure(VTMessagearray[i].id,VTMessagearray[i].dlc,VTMessagearray[i].data)
		count = VTMessagearray[i].count
		
		print ("%d: %s:" % (i+1,VTMessagearray[i].comment))
		print frame

		for n in range(0,count): 
			
			dev.send_driver(frame)
			time.sleep(VTMessagearray[i].delay)
			print frame
		c = raw_input("\nPress Enter to go ahead: \r\n")
	
	print ("key log file: %s" % (keylongfile))
	print "Finish Reversing!"
	
