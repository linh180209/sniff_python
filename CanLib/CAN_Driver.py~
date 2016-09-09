import sys
try:
    import serial
except ImportError:
    import socket
import struct
from CanLib.CAN_Packet import *
from CanLib.vtlog import *

class Operate:
	START = 0
	STOP = 1

class TypeCan:
	SERIAL = 1000
	SOCKET = 1001

class CANDriver:
	def __init__(self, type , port=None, bit_rate=0 ,name_dev=None):
		if(type != TypeCan.SERIAL and type != TypeCan.SOCKET):
			raise ValueError("Type not supported")
		self.type = type
		if(self.type == TypeCan.SERIAL):	
			self.ser = serial.Serial(port)
			self.set_bitrate(bit_rate)
			self.bitrate = bit_rate
		elif(self.type == TypeCan.SOCKET):
			self.name_dev = name_dev
	
	def set_bitrate(self, bitrate):
		if bitrate == 10000:
		    self.ser.write('S0\r')
		elif bitrate == 20000:
		    self.ser.write('S1\r')
		elif bitrate == 50000:
		    self.ser.write('S2\r')
		elif bitrate == 100000:
		    self.ser.write('S3\r')
		elif bitrate == 125000:
		    self.ser.write('S4\r')
		elif bitrate == 250000:
		    self.ser.write('S5\r')
		elif bitrate == 500000:
		    self.ser.write('S6\r')
		elif bitrate == 750000:
		    self.ser.write('S7\r')
		elif bitrate == 1000000:
		    self.ser.write('S8\r')
		else:
		    raise ValueError("Bitrate not supported")

	#0: start 1:stop
	def operate(self,flag):
		if not (flag == Operate.START or flag == Operate.STOP):
			print ("flag must be is Operate.START or Operate.STOP")
			exit()
		if(flag == Operate.START):
			if(self.type == TypeCan.SERIAL):
				self.ser.write('O\r')
			elif(self.type == TypeCan.SOCKET):
				try:
					socket.PF_CAN
					socket.CAN_RAW
				except:
					print("Python 3.3 or later is needed for native SocketCan")
					raise SystemExit(1)
				self.socket = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
				self.flag_run = True
				self.socket.bind((self.name_dev,))
				self.start_time = time.time()	
		elif(flag == Operate.STOP):
			if(self.type == TypeCan.SERIAL):
				self.ser.write('C\r')
			else:
				self.socket.close()	


	def receive_driver(self):
		if(self.type == TypeCan.SERIAL):
			try:
				# receive characters until a newline (\r) is hit
				rx = ""
				while (rx == "" or rx[-1] != '\r'):
					rx = ''.join([rx,self.ser.read()])
		
				# get packet parameters
				packet_id = int(rx[1:4], 16)

				# get the length
				length = int(rx[4])

				# get the payloads
				data = []

				i = 0
				while i < length:
					data.append(int(rx[5 + i*2:7 + i*2], 16))
					i += 1

				packet = CAN_Packet()
				packet.configure(packet_id, length, data,frtype='R')
	
			except:
			
				self.operate(Operate.STOP)
				time.sleep(0.5)		
				self.set_bitrate(self.bitrate)
				self.operate(Operate.START)
				return None,False

			return packet,True
		elif(self.type == TypeCan.SOCKET):
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
			packet.configure(id,len,[d0, d1, d2, d3, d4, d5, d6, d7],frtype='R',is_extended_id=is_extended)
			return packet,True

	def send_driver(self, packet):
		if(self.type == TypeCan.SERIAL):
			# add type, id, and dlc to string
			tx = "t%03X%d" % (packet.get_id(), packet.get_len())

			# add data bytes to string
			i = 0
			while i < packet.get_len():
				tx = ''.join([tx,("%02X" % packet.get_payload()[i])])
				i += 1

			# add newline (\r) to string
			tx = ''.join([tx,'\r'])

			self.ser.write(tx)
		elif(self.type == TypeCan.SOCKET):
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

	def sendframesfromfile(self,dev,filename):
		VTlf = VTlog()
		VTMessagearray = []
		VTMessagearray	= VTlf.parselog(filename)

		for i in range(0,len(VTMessagearray)):
			packet = CAN_Packet()
			packet.configure(VTMessagearray[i].id,VTMessagearray[i].dlc,VTMessagearray[i].data)
			count = VTMessagearray[i].count
	
			for n in range(0,count): 
				dev.send_driver(packet)
				time.sleep(VTMessagearray[i].delay)
				print (str(packet))
		return True

	def sendframesfromfile1b1(self,dev,filename):
		VTlf = VTlog()
		VTMessagearray = []
	
		VTMessagearray	= VTlf.parselog(filename)

		for i in range(0,len(VTMessagearray)):
			packet = CAN_Packet()
			packet.configure(VTMessagearray[i].id,VTMessagearray[i].dlc,VTMessagearray[i].data)
			count = VTMessagearray[i].count
	
			for n in range(0,count): 
				dev.send_driver(packet)
				time.sleep(VTMessagearray[i].delay)
				print (packet)
			if(self.type == TypeCan.SOCKET):
				c = input("Press Enter to go ahead!")
			else:
				c = raw_input("Press Enter to go ahead!")
	
		return True

