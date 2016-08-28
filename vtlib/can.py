import time

class FrameType:
	""" Enumerates the types of CAN frames """
	DataFrame = 1
	RemoteFrame = 2
	ErrorFrame = 3
	OverloadFrame = 4

class CategoryType:
	HFCDF = 1
	LFCDF = 2
	SDF = 3


class Frame(object):
	def __init__(self, id, dlc=0, data=[], count=1,frtype="S",delay=0.01,frame_type=FrameType.DataFrame,is_extended_id=False):
		# these 2 fields must be defined before 'id' and'data', otherwise
		# 'no attribute ' exception will be raised
		self.is_extended_id = is_extended_id
		self.dlc = dlc
		self.id = id
		self.data = data
		self.delay = delay #delay time between frames
		self.type = frtype #etc
		self.frame_type = frame_type
		self.count = count #count of this frames
		self.sibdcount = 1     #record the count of same id but data btye is different
		self.bytechangeflag = [0,0,0,0,0,0,0,0] #change flag of the byte
		self.bytechangecount = [0,0,0,0,0,0,0,0] #record the count of frame
		self.time = time.time()
		self.category = CategoryType.SDF
		self.comment = []

	def copy_comment(self,newcomment):
		self.comment = dict(newcomment)

	def get_comment(self):
		return self.comment

	@property
	def category(self):
		return self._category

	@category.setter
	def category(self, value):
		self._category = value

	@property
	def time(self):
		return self._time

	@time.setter
	def time(self, value):
		self._time = value

	@property
	def count(self):
		return self._count
	@count.setter
	def count(self, value):
		assert isinstance(value, int), 'id must be an integer'
		self._count = value

	@property
	def id(self):
		return self._id
	@id.setter
	def id(self, value):
		# ensure value is an integer
		assert isinstance(value, int), 'id must be an integer'
		# ensure standard id is in range
		if value >= 0 and value <= 0x7FF:
			self._id = value
		# otherwise, check if frame is extended
		elif self.is_extended_id and value > 0x7FF and value <= 0x1FFFFFFF:
			self._id = value
		# otherwise, id is not valid
		else:
			raise ValueError('CAN ID out of range')

	@property
	def data(self):
		# return bytes up to dlc length, pad with zeros
		data_len = min(self._dlc, len(self._data))
		result = self._data[:data_len]
		result.extend([0] * (8 - data_len))
		return result

	@data.setter
	def data(self, value):
		# data should be a list
		assert isinstance(value, list), 'CAN data must be a list'
		# data can only be 8 bytes maximum
		assert not len(value) > 8, 'CAN data cannot contain more than 8 bytes'
		# each byte must be a valid byte, int between 0x0 and 0xFF
		for byte in value:
			assert isinstance(byte, int), 'CAN data must consist of bytes'
			assert byte >= 0 and byte <= 0xFF, 'CAN data must consist of bytes'
			# data is valid
		self._data = value
	@property
	def frame_type(self):
		return self._frame_type

	@frame_type.setter
	def frame_type(self, value):
		assert value == FrameType.DataFrame or value == FrameType.RemoteFrame \
		or value == FrameType.ErrorFrame or value == FrameType.OverloadFrame, 'invalid frame type'
		self._frame_type = value

	@property
	def dlc(self):
		return self._dlc

	@dlc.setter
	def dlc(self, value):
		assert isinstance(value, int)
		assert value >= 0 and value <= 8, 'dlc must be between 0 and 8'
		self._dlc = value

	#return 0:if the 2 frame not same  1: 2 frames are the same 2: 2 frames have the same can id,but data is different
	def compare(self,frame):
		frame.bytechangeflag = [0,0,0,0,0,0,0,0]
		bytechangeflag = 0
		if(self.id == frame.id and self.dlc == frame.dlc):
			for i in range(self.dlc):				
				if(self.data[i] != frame.data[i]):										
					frame.bytechangeflag[i] = 1
					if self.bytechangecount[i] >= 0:
						bytechangeflag = 1
						self.bytechangecount[i] += 1	
					if((frame.time - self.time) <= 2):
						frame.category = CategoryType.HFCDF
					else:
						frame.category = CategoryType.LFCDF

			if bytechangeflag == 1:
				self.sibdcount += 1
				self.count += 1
				return 2  #two frames ID is same, but DATA is different
				
			else:
				self.count += 1
				return 1  #two frames is same include ID & DATA
		else:
			return 0	#complete different frames

	def add_comment(self,byte,c):
		if (byte != -1):
			s_byte = "byte%d"%byte
			self.comment[s_byte] = c

	def print_comment(self):
		result = "{\"type\":\"P\",\"count\":%d,\"id\":0x%X,\"dlc\":%d, signal:{"%(self.count,self.id,self.dlc)
		i = 0
		for c,b in self.comment.items():
			i = i + 1
			if i == len(self.comment):
				result = result + "\"%s\":%s}}"%(c,b)
			else: 
				result = result + "\"%s\":%s,"%(c,b)
		return result

	def print_log(self):
		result = "[{\"type\":\"%s\",\"count\":%d,\"id\":%d,\"dlc\":%d,\"data\":[%d,%d,%d,%d,%d,%d,%d,%d]}]" %("P",self.count,self.id,self.dlc,self.data[0],self.data[1],self.data[2],self.data[3],self.data[4],self.data[5],self.data[6],self.data[7])
		return result

	def __str__(self):
		if self.type == "R":
			result = "{type:%s,count:%d,\033[91mid:0x%X\033[0m,dlc:%d,data:[%X,%X,%X,%X,%X,%X,%X,%X]}"  %(self.type,self.count,self.id,self.dlc,self.data[0],self.data[1],self.data[2],self.data[3],self.data[4],self.data[5],self.data[6],self.data[7])
		else:
			result = "{type:%s,count:%d,id:0x%X,dlc:%d,data:[%X,%X,%X,%X,%X,%X,%X,%X]}" %(self.type,self.count,self.id,self.dlc,self.data[0],self.data[1],self.data[2],self.data[3],self.data[4],self.data[5],self.data[6],self.data[7])
		return result
