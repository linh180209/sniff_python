import os
import logging
import sys
import json
import demjson
import random
import time
from CAN_Packet import *

class Operate:
	START = 0
	STOP = 1

class CANSocket:
	def __init__(self,name_dev=None,filename=None):
		self.flag_run = False
		self.name_dev = name_dev
		
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

	def operate(self,flag):
		if(flag == Operate.START):
			try:
				socket.PF_CAN
				socket.CAN_RAW
			except:
				print("Python 3.3 or later is needed for native SocketCan")
				raise SystemExit(1)
		    	self.socket = socket.socket(socket.PF_CAN, socket.SOCK_RAW,
		                            socket.CAN_RAW)
			
			self.flag_run = True
			self.socket.bind((self.name_dev,))
			self.start_time = time.time()
		elif(flag == Operate.STOP):
			self.flag_run = False
			self.sock.close()

	def socket_recv(self):
		if(self.flag_run == False):
			print("device not running")
		packet_format = "=IB3xBBBBBBBB"
		packet_size = struct.calcsize(packet_format)

		packet_raw = self.socket.recv(packet_size)
		id, len, d0, d1, d2, d3, d4, d5, d6, d7 = struct.unpack(packet_format,
		                                                         packet_raw)

		# adjust the id and set the extended id flag
		is_extended = False
		if id & 0x80000000:
		    id &= 0x7FFFFFFF
		    is_extended = True
		
		packet = CAN_Packet()
		packet.configure(id,len,[d0, d1, d2, d3, d4, d5, d6, d7],is_extended_id=is_extended)
		return packet

	def socket_send(self, packet):
		if(self.flag_run == False):
			print("device not running")

		packet_format = "=IBBBBBBBBBBBB"

		# set the extended bit if a extended id is used
		id = packet.id
		if packet.is_extended_id:
		    id |= 0x80000000

		data = packet.get_payload()
		s_packet = struct.pack(packet_format, id, packet.get_len(), 0xff, 0xff, 0xff,
		                     data[0], data[1], data[2], data[3],
		                     data[4], data[5], data[6], data[7])

		self.socket.send(s_packet)

	def writelog(self,frbuffer=[]):
		print self.file_name
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
	
		
		
		
