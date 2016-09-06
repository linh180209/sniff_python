import json
from CanLib.CAN_Packet import *

class MessageFormat(object):
	def __init__(self,file_json):
		self.file_name = file_json
		self.message = []
		self.parse_json()

	def parse_json(self):
		with open(self.file_name, 'r') as f:
			db = json.load(f)
			for m in db['messages']:
				message = Message_json()
				message.configure(int(m['id'],0),m['name'])

				# iterate over signals
				for s_bit, signal in m['signals'].items():
					# parse offset and factor if set
					if 'offset' in signal:
						if 'factor' in signal:
							message.configure_signals(signal['name'], int(s_bit), signal['bit_length'],offset = int(signal['offset']), factor = int(signal['factor']))
						else:
							message.configure_signals(signal['name'], int(s_bit), signal['bit_length'],offset = int(signal['offset']))
					else:
						if 'factor' in signal:
							message.configure_signals(signal['name'], int(s_bit), signal['bit_length'], factor = int(signal['factor']))
						else:
							message.configure_signals(signal['name'], int(s_bit), signal['bit_length'])

				self.message.append(message)

	def parse_packet(self, packet):
		if not isinstance(packet, CAN_Packet):
			print ('invalid packet')
			exit()
		for m in self.message:
			if m.id == packet.get_id():
                		return m.parse_message(packet)
	

class Message_json(object):
	def __init__(self):
		pass

	def configure(self,id,name):
		assert isinstance(id, int), 'id must be an integer'
		self.id = id
		self.name = name
		self.name_signal = []
		self.start_bit = []
		self.length = []
		self.factor = []
		self.offset = []

	def configure_signals(self, name, start_bit, length, factor=1, offset=0):
		#check start bit
		if not isinstance(start_bit, int):
			print ('start_bit must be an integer')
			exit()

		#check length
		if not isinstance(length, int):
			print ('length must be an integer')
			exit()

		#check factor
		if not isinstance(factor, int):
			print ('factor must be an integer')		
			exit()

		#check offset
		if not isinstance(offset, int):
			print ('offset must be an integer')
			exit()
		

		self.name_signal.append(name)
		self.start_bit.append(start_bit)
		self.length.append(length)
		self.factor.append(factor)
		self.offset.append(offset)

	def parse_message(self, packet):
		if not isinstance(packet, CAN_Packet):
			print ('invalid packet')
			exit()

		# combine 8 data bytes into single value
		packet_value = 0
	
		i = 0
		while(i < packet.get_len()):
			if packet.get_payload()[i] != None:
				packet_value = packet_value + (packet.get_payload()[i] << (8 * i))
			i += 1
		
		result_signals = {}
		
		for i in range(len(self.name_signal)):
			
			# find the last bit of the singal
			end_bit = self.length[i] + self.start_bit[i]
			
			# compute the mask
			mask = 0
			j = self.start_bit[i]
			while j < end_bit:
				mask = mask + 2**j
				j += 1

			# apply the mask, then downshift
			value = (packet_value & mask) >> self.start_bit[i]
			value = value * self.factor[i] + self.offset[i]
			result_signals.update({self.name_signal[i]:value})

		return result_signals
			
