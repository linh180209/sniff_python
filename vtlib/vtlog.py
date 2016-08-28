from vtlib import can
import os
import logging
import sys
import json
import demjson
import random
import time

#This function is to define VTMessage class and VTlog, wirtelog and parselog. 
#Author: BensonYang
#Date: 20072016

class VTlog:
	def __init__(self,filename=None):
		
		FILEPATH = os.getcwd()
		FILEPATH = FILEPATH + '/logfolder/'
		self.file_path = FILEPATH
		rondc = random.randint(0,10000000)
		systime = time.strftime('--%Y-%m-%d-%H-%M-',time.localtime(time.time()))
		namelog = sys.argv[0][:len(sys.argv[0])-3] + systime + str(rondc) +".json"
		self.file_name = FILEPATH+namelog
		command = "python "
		for i in range(0,len(sys.argv)):
			command = command + "%s "%sys.argv[i]


	def writelog(self,frbuffer=[]):
		array = []
		for i in range(len(frbuffer)):
			writestr = [{"type":frbuffer[i].type,"count":frbuffer[i].count,"id":frbuffer[i].id,"dlc":frbuffer[i].dlc,"data":frbuffer[i].data,"delay":frbuffer[i].delay,"comment":frbuffer[i].comment}]
			array.append(writestr)			
		demjson.encode_to_file(self.file_name,array,encoding='utf-8', overwrite=True)			
		return self.file_name

	def parselog(self,filename):
		array = []
		#filename = self.file_path + filename	

		db = demjson.decode_file(filename)
		
		for k in range(0,len(db)):
			db[k] = str(db[k])[1:-1]
			db[k] = eval(db[k])			
			try:
				vtm = VTMessage(db[k]['id'],db[k]['dlc'],db[k]['data'],db[k]['count'],db[k]['delay'],db[k]['type'],db[k]['comment'])
			except:
				vtm = VTMessage(db[k]['id'],db[k]['dlc'],db[k]['data'],db[k]['count'],0.01,db[k]['type'],None)
		
			array.append(vtm)   # add the vt message to array
					
		return array

	def logfrarray2file(self,VTlogfile,array_f,frtype = "P",frcomment = ""):

		#Record broudgroud frames of testing bus
		vtmsgbuffer = []
		
		for i in range(len(array_f)):
			vtmsg = VTMessage(array_f[i].id,8,array_f[i].data,array_f[i].count,0.01,array_f[i].type,frcomment)
			vtmsgbuffer.append(vtmsg)

		logname = VTlogfile.writelog(vtmsgbuffer)
	
		return logname
			

class VTMessage:
	def __init__(self,canid=0x01,dlc=8,data=[],count=1,delay=0.01,typestr="p",comment=None):
		self.id = canid
		self.dlc = dlc
		self.data = data
		self.count = count	#cycle count
		self.delay = delay	#delay time between frames
		self.type = typestr	#frame type
		self.comment = comment	#comment for frmame

	def __str__(self):
		s = "Frame: ID=0x%X, %d, data=%s, Cycle Count: %d, delay: %fs, comment: %s \n" % (self.id, self.dlc, self.data, self.count, self.delay, self.comment)
		return s
	
