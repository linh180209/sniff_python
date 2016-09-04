import serial
from CAN_Packet import *
from CAN_Socket import *

class Operate:
	START = 0
	STOP = 1

class CANDriver:
	def __init__(self, port, bit_rate):
		self.ser = serial.Serial(port)
		self.set_bitrate(bit_rate)
		self.bitrate = bit_rate
	
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
			print 'flag must be is 0 or 1'
			exit()
		if(flag == Operate.START):
			self.ser.write('O\r')
		elif(flag == Operate.STOP):
			self.ser.write('C\r')


	def receive_driver(self):
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

	def send_driver(self, packet):
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

	def sendframesfromfile(self,dev,filename):
		VTlf = CANSocket()
		VTMessagearray = []
		VTMessagearray	= VTlf.parselog(filename)

		for i in range(0,len(VTMessagearray)):
			packet = CAN_Packet()
			packet.configure(VTMessagearray[i].id,VTMessagearray[i].dlc,VTMessagearray[i].data)
			count = VTMessagearray[i].count
	
			for n in range(0,count): 
				dev.send_driver(packet)
				time.sleep(VTMessagearray[i].delay)
				print str(packet)
        	return True

	def sendframesfromfile1b1(self,dev,filename):
		VTlf = CANSocket()
		VTMessagearray = []
	
		VTMessagearray	= VTlf.parselog(filename)

		for i in range(0,len(VTMessagearray)):
			packet = Packet()
			packet.configure(VTMessagearray[i].id,VTMessagearray[i].dlc,VTMessagearray[i].data)
			count = VTMessagearray[i].count
	
			for n in range(0,count): 
				dev.send_driver(packet)
				time.sleep(VTMessagearray[i].delay)
				print packet
			c = raw_input("Press Enter to go ahead!")
	
		return True

