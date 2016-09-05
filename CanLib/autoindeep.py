import sys
from CAN_Packet import *
from CAN_Driver import *
from vtlog import *
import random
import math
import time
import os

# This function is to test the affection of data bytes, the key id is input payload

def analyzebytes(dev,keyidarray):
	
	lognamearray = []
	keyinfo = [] #temprary using to record keyid and its bytes

	for n in range(0,len(keyidarray)):
		
		VTlogfile = VTlog()
		vtmsgbuffer = []
		data = [0 for x in range(8)]
		fr = CAN_Packet()  
		fr.configure(keyidarray[n],8,data)#can id/length
		

		print "\nStep 1:"

		for count in range(0,8):
			while data[count] < 255:
				fr.data = data
				time.sleep(0.005)  #5ms/frame
				dev.send_driver(fr)
				vtmsg = VTMessage(fr.id,8,fr.get_payload(),1,0.01,"S","comment")
				vtmsgbuffer.append(vtmsg)
				print fr
				data[count] += 1
				print data[count]
			fuzzcomment = raw_input("\nplease comment the affection: \r\n")
			vtmsgbuffer[-1]= VTMessage(fr.id,8,fr.get_payload(),1,0.01,"k",fuzzcomment)
			##########temprary using
			if fuzzcomment <> "":
				keyinfo.append([fr.id,count+1,fuzzcomment])
			##########
			print vtmsgbuffer[-1]

		debugflag = 0
	
		if debugflag:
			print "\nStep 2: "

			data = [0 for x in range(8)]
			for count in range(0,8,2):
				while data[count] < 255:
					fr.data = data
					time.sleep(0.005)  #5ms/frame
					dev.send_driver(fr)
					vtmsg = VTMessage(fr.id,8,fr.get_payload(),1,0.01,"S","comment")
					vtmsgbuffer.append(vtmsg)
					print fr
					data[count] += 1
					data[count+1] = data[count]
					print data[count]
				fuzzcomment = raw_input("\nplease comment the affection: \r\n")
				vtmsgbuffer[-1]= VTMessage(fr.id,8,fr.get_payload(),1,0.01,"K",fuzzcomment)
				print vtmsgbuffer[-1]
	

			print "\nStep 3:"
			data = [0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF]
			for count in range(0,8,2):
				while data[count] < 255:
					fr.data = data
					time.sleep(0.005)  #5ms/frame
					dev.send_driver(fr)
					vtmsg = VTMessage(fr.id,8,fr.get_payload(),1,0.01,"S","comment")
					vtmsgbuffer.append(vtmsg)
					print fr
					data[count] += 1
					data[count+1] -= 1
					print data[count]
				fuzzcomment = raw_input("\nplease comment the affection: \r\n")
				vtmsgbuffer[-1]= VTMessage(fr.id,8,fr.get_payload(),1,0.01,"K",fuzzcomment)
				print vtmsgbuffer[-1]

			print "\nStep 4:"
			data = [0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF,0X00]
			for count in range(0,8,2):
				while data[count+1] < 255:
					fr.data = data
					time.sleep(0.005)  #5ms/frame
					dev.send_driver(fr)
					vtmsg = VTMessage(fr.id,8,fr.get_payload(),1,0.01,"S","comment")
					vtmsgbuffer.append(vtmsg)
					print fr
					data[count] -= 1
					data[count+1] += 1
					print data[count]
				fuzzcomment = raw_input("\nplease comment the affection: \r\n")
				vtmsgbuffer[-1]= VTMessage(fr.id,8,fr.get_payload(),1,0.01,"K",fuzzcomment)
				print vtmsgbuffer[-1]

			print "\nStep 5:"
			data = [0 for x in range(8)]
			for count in range(0,8,4):
				while data[count+1] < 255:
					fr.data = data
					time.sleep(0.005)  #5ms/frame
					dev.send_driver(fr)
					vtmsg = VTMessage(fr.id,8,fr.get_payload(),1,0.01,"S","comment")
					vtmsgbuffer.append(vtmsg)
					print fr
					data[count] += 1
					data[count+1] = data[count]
					data[count+2] = data[count]
					data[count+3] = data[count]
					print data[count]
				fuzzcomment = raw_input("\nplease comment the affection: \r\n")
				vtmsgbuffer[-1]= VTMessage(fr.id,8,fr.get_payload(),1,0.01,"K",fuzzcomment)
				print vtmsgbuffer[-1]

	
			print "\nStep 6:"
			data = [0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00, 0xFF, 0xFF]
			for count in range(0,8,4):
				while data[count+1] < 255:
					fr.data = data
					time.sleep(0.005)  #5ms/frame
					dev.send_driver(fr)
					vtmsg = VTMessage(fr.id,8,fr.get_payload(),1,0.01,"S","comment")
					vtmsgbuffer.append(vtmsg)
					print fr
					data[count] += 1
					data[count+1] = data[count]
					data[count+2] -= 1
					data[count+3] = data[count+2]
					print data[count]
				fuzzcomment = raw_input("\nplease comment the affection: \r\n")
				vtmsgbuffer[-1]= VTMessage(fr.id,8,fr.get_payload(),1,0.01,"K",fuzzcomment)
				print vtmsgbuffer[-1]	

		lognamearray.append(VTlogfile.writelog(vtmsgbuffer))

	print "\n\n============================================================="
	for i in range(0,len(keyinfo)):		
		print ("key id: 0x%X; key byte: %s" % (keyinfo[i][0],keyinfo[i][1]))
	for i in range(0,len(lognamearray)):
		print("Log file: %s" % (lognamearray[i]))
	print "\n=============Finished Autoindeep!=============================="
	print "\n==============================================================="

	return keyinfo

