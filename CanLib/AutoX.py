import socket
import sys
import multiprocessing
try:
    import queue
except ImportError:
    import Queue as queue

class AutoX(object):
	def __init__(self):
		pass

	def configure(self,address,port,log_file):
		self.address = address
		self.port = port
		self.log_file = log_file
		
		#init log file
		self.logging.basicConfig(filename=log_file,level=logging.DEBUG,format='%(asctime)s %(message)s',datefmt='%m/%d/%Y-%I:%M:%S-%p')
		#init process receive and send socket
		self.recv_socket = multiprocessing.Process(target=self.receive_socket)
		self.send_socket = multiprocessing.Process(target=self.send_socket)

		#init queue receive and send
		self.recv_queue = multiprocessing.Queue()
		self.send_queue = multiprocessing.Queue()

	def connect(self):
		#check address
		if(self.address == None):
			print 'Address not value'
			exit()
		
		#check port
		if(self.port == None):
			print 'Port not value'
			exit()

		#check log file
		if(self.log_file == None):
			print 'Log File not value'
			exit()

		# Create a TCP/IP socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		# Connect the socket to the port where the server is listening
		server_address = (self.address, self.port)
		
		#connect
		self.sock.connect(server_address)

		#start process receive and send
		self.recv_socket.start()
		self.send_socket.start()

	def disconnect(self):
		if(self.sock ! = None):
			self.recv_socket.terminate()
			self.send_socket.terminate()
			self.sock.close()
	
	def receive_socket(self):
		while True:
			if(self.sock != None):
            			packet = self.sock.recv(1024)
				self.recv_queue.put(packet)

	def send_socket(self):
		while True:
			if(self.sock != None):
				packet = self.send_queue.get()
				self.sock.sendall(packet)
		
	def getXTraffic(self,timeout = 1, filter=None):
		try:
			start_time = time.time()
			while True:
				packet = self.recv_queue.get(timeout=timeout)
			if not filter:
				return packet
			elif filter == packet.get_id():
				return packet
			# ensure we haven't gone over the timeout
			if time.time() - start_time > timeout:
				return None

		except queue.Empty:
			return None

		
	def replayXTracffic(self,message):
		if(self.sock != None):
			self.send_queue.put(message)

	def uploadXLog(self):
		pass
	
	
	def write_XLog(self,message):
		self.logging.debug(message)
		
	

	
	
	
