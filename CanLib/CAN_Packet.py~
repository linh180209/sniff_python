import time

class PacketType:
	""" Enumerates the types of CAN Packets """
	DataPacket = 1
	RemotePacket = 2
	ErrorPacket = 3
	OverloadPacket = 4

class CategoryType:
	HFCDF = 1
	LFCDF = 2
	SDF = 3

class CAN_Packet(object):

	def __init__(self):
		self.configure(0x0,0,[0,0,0,0,0,0,0,0])
		

	def validate(self,value, v_type):
		#validate CAN ID 
		if(v_type == 0):

			if not isinstance(value, int):
				print ("CAN ID should be an integer!")
				exit()

			# validate CAN ID
			if value >= 0 and value <= 0x7FF:
				self.id = value
			else:
				raise ValueError('CAN ID is not valide or not supported!')

		#validate packet length
		elif(v_type == 1):
			if not isinstance(value, int):
				print ("length value must be interger")
				exit()
			
			if not (value >= 0 and value <= 8):
				print ("not valid length")
				exit()

			self.len = value

		#check data
		elif(v_type == 2):
			# data should be a list
			if not isinstance(value, list):
				print ("CAN data must be a list")
				exit()
			
			# data can only be 8 bytes maximum
			if (len(value) > 8):
				print ("CAN payload more than 8 not supported")
				exit()

			# each byte must be a valid byte, int between 0x0 and 0xFF
			for byte in value:
				if not isinstance(byte, int):
					print ("invalid CAN payloads")
					exit()
				if not (byte >= 0 and byte <= 0xFF):
					print ("invalid CAN payloads")
					exit()

			self.data = value
		#check count
		elif(v_type == 3):
			if not isinstance(value, int):
				print ("count must be a interger")
				exit()
			self.count = value

		#check frtype
		elif(v_type == 4):
			self.type = value
	
		#check delay
		elif(v_type == 5):
			self.delay = value
		
		#check packet type
		elif(v_type == 6):
			if not isinstance(value, int):
				print ("Packet Type must be a interger")
				exit()
			if(value < PacketType.DataPacket or value > PacketType.OverloadPacket):
				print ("Packet Type not value")
				exit()
			self.frame_type = value
				

	def get_id(self):
		return self.id

	def get_payload(self):
		data_len = min(self.len, len(self.data))
		result = self.data[:data_len]
		result.extend([0] * (8 - data_len))
		return result
	
	def get_len(self):
		return self.len
	
	def configure(self,id, len=0, payload=[],count=1,frtype="S",delay=0.01,frame_type=PacketType.DataPacket,is_extended_id=False):
		#set id
		self.validate(id,0)
		
		#set len
		self.validate(len,1)

		#set payload
		self.validate(payload,2)
		
		#set count: count of this frames
		self.validate(count,3)
		
		#set frtype: etc
		self.validate(frtype,4)
		
		#set delay: delay time between frames
		self.validate(delay,5)
		
		#set frame_type
		self.validate(frame_type,6)		

		#set is_extended_id	
		self.is_extended_id = is_extended_id
		
		#record the count of same id but data btye is different
		self.sibdcount = 1

		#change flag of the byte
		self.bytechangeflag = [0,0,0,0,0,0,0,0] 

		#record the count of packet
		self.bytechangecount = [0,0,0,0,0,0,0,0]
		
		#set time at create
		self.time = time.time()
		
		#set category
		self.category = CategoryType.SDF

		#set comment
		self.comment = {}
				
	#return 0:if the 2 packet not same  1: 2 packets are the same 2: 2 packets have the same can id,but data is different
	def compare(self,packet):
		packet.bytechangeflag = [0,0,0,0,0,0,0,0]
		bytechangeflag = 0
		if(self.id == packet.id and self.len == packet.len):
			for i in range(self.len):				
				if(self.data[i] != packet.data[i]):
					packet.bytechangeflag[i] = 1
					if self.bytechangecount[i] >= 0:
						bytechangeflag = 1
						self.bytechangecount[i] += 1	
					if((packet.time - self.time) <= 2):
						packet.category = CategoryType.HFCDF
					else:
						packet.category = CategoryType.LFCDF

			if bytechangeflag == 1:
				self.sibdcount += 1
				self.count += 1
				return 2  #two packets ID is same, but DATA is different
				
			else:
				self.count += 1
				return 1  #two packets is same include ID & DATA
		else:
			return 0	#complete different packets

	def add_comment(self,byte,c):
		if (byte != -1):
			s_byte = "byte%d"%byte
			self.comment[s_byte] = c

	def print_comment(self):
		result = "{\"type\":\"P\",\"count\":%d,\"id\":0x%X,\"dlc\":%d, signal:{"%(self.count,self.id,self.len)
		i = 0
		for c,b in self.comment.items():
			i = i + 1
			if i == len(self.comment):
				result = result + "\"%s\":%s}}"%(c,b)
			else: 
				result = result + "\"%s\":%s,"%(c,b)
		return result

	def print_log(self):
		result = "[{\"type\":\"%s\",\"count\":%d,\"id\":%d,\"dlc\":%d,\"data\":[%d,%d,%d,%d,%d,%d,%d,%d]}]" %("P",self.count,self.id,self.len,self.get_payload()[0],self.get_payload()[1],self.get_payload()[2],self.get_payload()[3],self.get_payload()[4],self.get_payload()[5],self.get_payload()[6],self.get_payload()[7])
		return result

	def __str__(self):
		if self.type == "R":
			result = "{type:%s,count:%d,\033[91mid:0x%X\033[0m,dlc:%d,data:[%X,%X,%X,%X,%X,%X,%X,%X]}"  %(self.type,self.count,self.id,self.len,self.get_payload()[0],self.get_payload()[1],self.get_payload()[2],self.get_payload()[3],self.get_payload()[4],self.get_payload()[5],self.get_payload()[6],self.get_payload()[7])
		else:
			result = "{type:%s,count:%d,id:0x%X,dlc:%d,data:[%X,%X,%X,%X,%X,%X,%X,%X]}" %(self.type,self.count,self.id,self.len,self.get_payload()[0],self.get_payload()[1],self.get_payload()[2],self.get_payload()[3],self.get_payload()[4],self.get_payload()[5],self.get_payload()[6],self.get_payload()[7])
		return result

