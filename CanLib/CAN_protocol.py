from CAN_Packet import *
import multiprocessing

try:
    import queue
except ImportError:
    import Queue as queue
import time

class Type:
	OBD = 1
	UDS = 2

class Operate:
	START = 0
	STOP = 1

class Type_Packet:
	TYPE_0 = 0
	TYPE_1 = 1
	TYPE_2 = 2

class ISOTP_driver(object):

	def __init__(self,can_dev):
		self.can_dev = can_dev
		self.queue_recv = multiprocessing.Queue()
		self.queue_send = multiprocessing.Queue()

	def operate(self,flag):
		if(flag == Operate.START):
			self.end = False
			self.can_dev.operate(Operate.START)
			self.process_recv = multiprocessing.Process(target=self.task_receive)
			self.process_send = multiprocessing.Process(target=self.task_send)
			self.process_recv.start()
			self.process_send.start()
		elif(flag == Operate.STOP):
			self.end = True
			self.process_recv.terminate()
			self.process_send.terminate()
			self.can_dev.operate(Operate.STOP)
		else:
			print 'flag Operate must to be Operate.START or Operate.STOP'	
			exit();
		
	def task_receive(self):
		while not self.end:
            		packet = self.can_dev.receive_driver()
			try:
				self.queue_recv.put(packet)
			except queue.Full:
				pass
	
	def task_send(self):
		while not self.end:
			packet = self.queue_send.get()
			self.can_dev.send_driver(packet)

	def send_packet(self,packet):
		self.queue_send.put(packet)

	#def get_packet(self, timeout=1, filter=None):
	#	try:
	#		s_time = time.time()
	#		while True:
	#			if time.time() - s_time > timeout:
	#				return None
	#			packet = self.queue_recv.get(timeout=timeout)
	#			if not filter:
	#				return packet
	#			elif filter == packet.get_id():
	#				return packet
	#	except queue.Empty:
	#		return None
	
	def get_packet(self, timeout=1, filter=None):
		try:
			start_time = time.time()
			while True:
				msg,devstatusflag = self.queue_recv.get(timeout=timeout)
				print '0x%X'%msg.get_id()
				if msg == None:
					return None,False
				if not filter:
					return msg,True
				elif filter == msg.get_id():
					return msg,True
				elif devstatusflag == False:
					return None,False
				# ensure we haven't gone over the timeout
				if time.time() - start_time > timeout:
					return None,True

		except queue.Empty:
		    return None,True

	def get_packet_filter_array(self, timeout=1, filterarray=[]):
		try:
			start_time = time.time()
			while True:
				msg, devstatusflag = self.queue_recv.get(timeout=timeout)

				if msg == None:
					return None,False
				#print msg
				if not filterarray:
					return msg,True
				elif msg.id not in filterarray:
					return msg,True
				elif devstatusflag == False:
					return None,False
				# ensure we haven't gone over the timeout
				if time.time() - start_time > timeout:
					return None,True

		except queue.Empty:
				return None,True


	def generate_OBD(self,id_ms,length_ms,data_ms):
		length_data = length_ms + 1
		data = []
		data.append(length_ms)
		for d in data_ms:
			data.append(d)
		p = CAN_Packet()
		p.configure(id_ms,length_data,data)
		return p
	
	def generate_UDS(self,id_ms,length_ms,data_ms):
		if (length_ms > 7):
			result = []
			data = []
			data.append(0x10 + (length_ms >> 8))
			data.append(length_ms & 0xFF)
			number_byte_send = 6
			for i in range(6):
				data.append(data_ms[i])
			sf = CAN_Packet()
			sf.configure(id_ms,8,data)
			result.append(sf)
			number_packet = 1

			while True:
				if(length_ms - number_byte_send > 7):
					length_data = 8
				else:
					length_data = length_ms - number_byte_send + 1
				data = []
				data.append(0x20 + number_packet)
				data = data + data_ms[number_byte_send:number_byte_send+length_data - 1]
				sf = CAN_Packet()
				sf.configure(id_ms,length_data,data)
				result.append(sf)
				number_byte_send += (length_data-1)
				if(number_byte_send >= length_ms):
					break;
				number_packet += 1
				if(number_packet > 15):
					number_packet = 0
			return result
		else:
			result = []
			length_data = length_ms + 1
			data = []
			data.append(length_ms)
			for d in data_ms:
				data.append(d)
			p = CAN_Packet()
			p.configure(id_ms,length_data,data)
			result.append(p)
			return result

	def generate_packet(self,id_ms,length_ms,data_ms,type):
		if not isinstance(id_ms, int):
			print 'CAN ID must be an integer'
			exit()
		if not isinstance(length_ms, int):
			print 'length must be an integer'
			exit()
		if not isinstance(data_ms, list):
			print 'Payloads must be a list'
			exit()
	
		if(type == Type.OBD):
			return self.generate_OBD(id_ms,length_ms,data_ms)
			
		elif(type == Type.UDS):
			return self.generate_UDS(id_ms,length_ms,data_ms)
		else:
			print 'type must to Type.UDS or Type.OBD'
			return None
	
	# single frame	
	def parse_signle_frame(self,packet):
		# init
        	self.byte_count = 0
        	self.s_number = 0
            
		# validate length
		self.length_ms = packet.get_payload()[0] & 0xF
            
		if self.length_ms < 1 or self.length_ms > 7:
			print "invalid length for single packet"
			exit()
			
		return packet.get_payload()[1:self.length_ms+1]

	def parse_first_frame(self,packet):
		# init
		self.byte_count = 0
        	self.s_number = 0

		# get byte 0
		temp = (packet.get_payload()[0] & 0xF) << 8 
		# get byte 1
		self.length_ms = temp + packet.get_payload()[1]

		#get data
		self.data_ms = []
		if(self.length_ms < 6):
			i = 2;
			while i < self.length_ms+2:
				self.data_ms.append(packet.get_payload()[i])
				self.byte_count += 1
				i += 1
		else:
				
			i = 2;
			while i < 8:
				self.data_ms.append(packet.get_payload()[i])
				self.byte_count += 1
				i += 1

		self.s_number += 1
		return None

	def parse_consecutive_frame(self,packet):
		if(self.length_ms == None):
			no_packet = packet.get_payload()[0] & 0xF
			if(no_packet == self.s_number):
				if(self.length_ms - self.byte_count < 7):
					i = 1
					while (i < self.length_ms - self.byte_count + 1):
						self.data_ms.append(packet.get_payload()[i])
						self.byte_count += 1
						i += 1
				else:
					i = 1
					while (i < 8):
						self.data_ms.append(packet.get_payload()[i])
						self.byte_count += 1
						i += 1

				if self.byte_count == self.length_ms:
					return self.data_ms
				elif self.byte_count > self.length_ms:
					print 'data length not match'
					exit()
				self.s_number += 1
				if (self.s_number > 15):
					self.s_number = 0
			else:
				print 'sequence number not match'
				exit()								
		else:
			print 'Need have before first Packet'
			exit()

	def parse_packet(self, packet):
		# get protocol control information
		type = (packet.get_payload()[0] & 0xF0) >> 4
		
		#Single frame
		if(type == Type_Packet.TYPE_0):
			return self.parse_signle_frame(packet)
		#First frame
		elif(type == Type_Packet.TYPE_1):
			return self.parse_first_frame(packet)
		#Consecutive frame
		elif(type == Type_Packet.TYPE_2):
			return self.parse_consecutive_frame(packet)


	def packet_create(self,ecu_id,mode,payload,driver_type,timeout=2):
		if(driver_type == Type.OBD):
			#generate packet
			packet_request = self.generate_packet(ecu_id,2,[mode, payload],Type.OBD)
			
			#send packet
			self.queue_send.put(packet_request)
			
			#receive reponse message
			response,flag = self.get_packet(timeout,ecu_id + 0x20)
			
			if(response != None):
				return self.parse_packet(response)
			else:
				return None	
			
		elif(driver_type == Type.UDS):
			result = None
			#generate a request
        		packet_request = self.generate_packet(ecu_id,len(payload) + 1,[mode] + payload,Type.UDS)
			
			# send the packet request
			for f in packet_request:
				self.queue_send.put(f)

			start_ts = time.time()
        		while result == None:
				response,flag = self.get_packet(filter=ecu_id + 0x20)
				if response:
					result = self.parse_packet(response)
				if time.time() - start_ts > timeout:
					return None

			return result
			
				
