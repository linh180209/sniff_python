import getopt,sys
sys.path.append("..")
import struct
import socket
import random
import time
import select
import string
from const import *
from CanLib.CAN_Driver import *
from CanLib.CAN_Socket import *
from CanLib.CAN_Packet import *


# This program is to simulate ECU that could interact with diagnostic device via UDS protocal
# sudo python udsspoof.py /dev/ttyACM0 125000


CONST = Const()

DEBUG 		= 1
VIN 		= "LC0CD4C38G1016472"
#VIN 		= "VISUALTHREAT88888"
VIN 		= "VTHIIIIIIIIIIIIII"
#VIN 		= "VVVVVVVVVVVVVVVVV"
#VIN = "WAUZZZ8V9FA149850"
#VIN = "1G1ZT53826F109149"
#VIN = "5YJSA1S2FEFA00001"
DATA_ALPHA     	= 0
DATA_ALPHANUM  	= 1
DATA_BINARY    	= 2

#Globals
running = 0
verbose = 1
no_flow_control = 0
fuzz_level = 0
keep_spec = 0
vin = []
start_tv = None
pending_data = 0
gm_data_by_id = CAN_Packet()
gm_lastcms = 0

# This is for flow control packets */
gBuffer = []
gBufSize = None
gBufLengthRemaining = None
gBufCounter = None


#for log
logdataobj = []

def usage(self, app, msg=None):
	print("Simulates UDS responses")
	if (msg != None):
		print("%s\n"% msg)
	print("Usage: %s [options] <can_interface>\n" %app)
	print("\t-z\t\tIncrease fuzz level\n")
	print("\t-v\t\tVerbose\n");
	print("\t-l <logfile>\tLog output to file instead of STDOUT\n");
	print("\t-c\t\tDon't fuzz ISOTP Spec, just data\n");
	print("\t-F\t\tDisable flow control (Functional Addressing)\n");
	print("\t-V <vin>\tSpecify VIN (Default: %s)\n" %VIN);
	print("\n");
	exit(1);

# Prints binary data in hex format
def print_bin(bin, size):
	for i in range(0,size):
		log = "%02X " %bin[i]
		plog(log)
	plog("\n")

def plog(fmt):
	print fmt

def print_pkt(fr):
	print fr

# Generates data into a buff and returns it.
def gen_data(scope, size):
	charset = None
	buf= []
	byte = None
	num = None
	i = None
	for i in range(size):
		buf.append(0)

	if(scope == DATA_ALPHA):
		charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
		for i in range(size):
			buf[i] = charset[random.randint(0,len(charset)-1)]
	elif(scope == DATA_ALPHANUM):
		charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
		for i in range(size):
			num = random.randint(0,len(charset)-1)
			byte = charset[num]
			if (DEBUG == 1):
				print("DEBUG: random byte[%d] = %d %s\n"%(i,num,byte))
			buf[i] = byte
	elif(scope == DATA_BINARY):
		for i in range(size):
			buf[i] = random.randint(0,255)
	return buf

# If a flow control packet comes in, push out more data
# This isn't fully supported, just a hack at the moment
def flow_control_push_to(dev,id):
	frame = CAN_Packet()
	frame.id = id
	nbytes = None
	if(no_flow_control == 1):
		return
	if(verbose):
		plog("FC: Flushing ISOTP buffers\n")
	while(gBufLengthRemaining > 0):
		if(gBufLengthRemaining > 7):
			frame.len = 8
			frame.data[0] = gBufCounter
			frame.data[1:1+7] = gBuffer[(gBufSize-gBufLengthRemaining):(gBufSize-gBufLengthRemaining+7)]
			dev.send_driver(frame)
			logdataobj.append(frame)
			gBufCounter = gBufCounter + 1
			gBufLengthRemaining = gBufLengthRemaining - 7
		else:
			frame.len = gBufLengthRemaining + 1
			frame.data[0] = gBufCounter
			frame.data[1:1+16] = gBuffer[(gBufSize-gBufLengthRemaining):(gBufSize-gBufLengthRemaining+16)]
			dev.send_driver(frame)
			logdataobj.append(frame)
			gBufLengthRemaining = 0

def flow_control_push(dev):
	flow_control_push_to(dev, 0x7e8)

def isotp_send_to(dev, data, size, dest):
	frame = CAN_Packet()
	frame.id = dest
	left = size
#	datatemp = [0 for x in range(2048)]
	datatemp = []
	counter = None
	nbytes = None
	if(size > 256):      #could complete with isotp API
		return
	if(size < 7):
		frame.len = size + 1
		#frame.data[0] = size
		#frame.data[1:1+size] = data
		datatemp.append(size)
		#datatemp.append(size)
		for n in range(0,size):
			datatemp.append(data[n])

		frame.data = datatemp
		#print "mark"
		#print data
		#print datatemp
		#print frame.data
		print frame
		dev.send_driver(frame)
		logdataobj.append(frame)
	else:
		frame.len = 8;
		datatemp.append(0x10)
		#datatemp[0] = 0x10
		#frame.data[0] = 0x10
		if(fuzz_level > 2 and keep_spec == 0):
			#frame.data[1] = random.randint(0,255)
			datatemp.append(random.randint(0,255))
			print("Breaking ISOTP specs real size = %d reported size = %d\n", size, frame.data[1])
		else:
			#frame.data[1] = size-1
			datatemp.append(size-1)
			#datatemp[1] = size-1
		for n in range(0,6):
			datatemp.append(data[n])
		#datatemp[2:2+6] = data
		#frame.data[2:2+6] = data
		#frame.data = datatemp[:8]
		#print datatemp
		frame.data = datatemp
		#print data
		#print datatemp
		print frame
		dev.send_driver(frame)
		logdataobj.append(frame)
		left = left - 6
		counter = 0x21
		if(no_flow_control == 1):
			while(left > 0):
				if(left > 7):
					frame.len = 8
					frame.data[0] = counter
					frame.data[1:1+7] = data[(size-left):(size-left+7)]
					dev.send_driver(frame)
					logdataobj.append(frame)
					print frame
					counter = counter + 1
					left = left - 7
				else:
					frame.len = left + 1
					frame.data[0] = counter
					frame.data[1:1+16] = data[(size-left):(size-left+16)]
					dev.send_driver(frame)
					logdataobj.append(frame)
					print frame
					left = 0
		else:
			gBuffer[0:size] = data
			gBufSize = size
			gBufLengthRemaining = left
			gBufCounter = counter

def isotp_send(dev, data, size):
	isotp_send_to(dev, data , size, 0x7e8)


# Some UDS queries requiest periodic data.  This handles those
def handle_pending_data(dev):
	global gm_lastcms
	frame = CAN_Packet()
	frame.id = 0x01
	currcms = None
	i = None
	offset = None
	datacnt = None
	if(pending_data == 0):
		return
	currcms = (time.time() - start_tv) * 100
	if(CONST.IS_SET(pending_data,CONST.PENDING_READ_DATA_BY_ID_GM)):
		if(gm_data_by_id.data[0] == 0xFE):
			offset = 1
		else:
			offset = 0
		frame.id = gm_data_by_id.id
		frame.len = 8
		#Slow Rate
		if(gm_data_by_id.data[2 + offset] == 0x02):
			if (currcms - gm_lastcms > 1000):
				for i in range(3,gm_data_by_id.data[0]+1):
					frame.data[0] = gm_data_by_id.data[i]
					for datacnt in range(1,8):
						frame.data[datacnt] = random.randint(0,254)
						dev.send_driver(frame)
						logdataobj.append(frame)
						if(verbose > 1):
							log = "  + Sending GM data (%02X) at a slow rate\n" %sframe.data[0]
							plog(log)
				gm_lastcms = currcms
		#Medium Rate
		elif(gm_data_by_id.data[2 + offset] == 0x03):
			if (currcms - gm_lastcms > 100):
				for i in range(3,gm_data_by_id.data[0]+1):
					frame.data[0] = gm_data_by_id.data[i]
					for datacnt in range(1,8):
						frame.data[datacnt] = random.randint(0,254)
						dev.send_driver(frame)
						logdataobj.append(frame)
						if(verbose > 1):
							log = "  + Sending GM data (%02X) at a medium rate\n" %frame.data[0]
							plog(log)
				gm_lastcms = currcms
		#Fast Rate
		elif(gm_data_by_id.data[2 + offset] == 0x04):
			if (currcms - gm_lastcms > 20):
				for i in range(3,gm_data_by_id.data[0]+1):
					frame.data[0] = gm_data_by_id.data[i]
					for datacnt in range(1,8):
						frame.data[datacnt] = random.randint(0,254)
						dev.send_driver(frame)
						logdataobj.append(frame)
						if(verbose > 1):
							log = "  + Sending GM data (%02X) at a fast rate\n"%frame.data[0]
							plog(log)
				gm_lastcms = currcms
		else:
			plog("Unknown subfunction timer\n")

def send_dtcs(dev, total,frame):
	resp = []
	i = None
	#for i in range(1024):
	#	resp.append(0)
	if(fuzz_level == 0):
		#resp[0] = frame.data[1] + 0x40
		#resp[1] = total

		
		resp.append(frame.data[1] + 0x40)
		resp.append(total)

		for i in range(0,(total*2+1),2):
			#resp[2+i] = 1
			#resp[2+i+1] = i
			resp.append(1)
			resp.append(i)			
			
		if(total == 0):
			isotp_send(dev, resp, 2)
		elif (total < 3):
			isotp_send(dev, resp, 2+(total*2))
		else:
			isotp_send(dev, resp, total*2)

	elif(fuzz_level == 1):
		#resp[0] = frame.data[1] + 0x40
		#resp[1] = random.randint(0,255)

		resp.append(frame.data[1] + 0x40)
		resp.append(random.randint(0,255))
		

		if (verbose):
			log = "Randomized total DTCs to %d real DTCs %d\n" %(resp[1],total)
			plog(log);
		for i in range(0,(total*2 + 1),2):
			#resp[2+i] = 1
			#resp[2+i+1] = i
			resp.append(1)
			resp.append(i)

		if(total == 0):
			isotp_send(dev, resp, 2)
		elif (total < 3):
			isotp_send(dev, resp, 2+(total*2))
		else:
			isotp_send(dev, resp, total*2)
	else:
		#resp[0] = frame.data[1] + 0x40
		#total = random.randint(0,127)
		#resp[1] = total

		resp.append(frame.data[1] + 0x40)
		resp.append(random.randint(0,127))
		
		if (verbose):
			log = "Randomized total DTCs to %d\n" %resp[1]
			plog(log)
		for i in range(0,(total*2 + 1),2):
			#resp[2+i] = random.randint(0,255)
			#resp[2+i+1] = random.randint(0,255)

			resp.append(random.randint(0,255))
			resp.append(random.randint(0,255))

		if (verbose):
			plog("DTC random data is:\n")
			print_bin(resp[2:], total*2)
		if(total == 0):
			isotp_send(dev, resp, 2)
		elif (total < 3):
			isotp_send(dev, resp, 2+(total*2))
		else:
			isotp_send(dev, resp, total*2)

def calc_vin_checksum(vin, size):
	w = [ 8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
	checksum = 0
	num = None
	print "mark"
	print vin
	print size
	for i in range(0,size):
		if((vin[i] == 'I') or (vin[i] == 'O') or (vin[i] == 'Q')):
			num = 0
		else:
			if((vin[i] >= '0') and (vin[i] <='9')):
				num = ord(vin[i]) - ord('0')
			if((vin[i] >= 'A') and (vin[i] <='I')):
				num = (ord(vin[i]) - ord('A')) + 1
			if((vin[i] >= 'J') and (vin[i] <='R')):
				num = (ord(vin[i]) - ord('J')) + 1
			if((vin[i] >= 'S') and (vin[i] <='Z')):
				num = (ord(vin[i]) - ord('S')) + 2
		checksum = checksum + num * w[i%len(w)]
	checksum = checksum % 11
	if (checksum == 10):
		return ord('X')
	return (ord('0') + checksum)

def send_error_snfs(dev,frame):
	resp = []
	if(verbose):
		plog("Responded with Sub Function Not Supported\n")
	resp.append(0x7f)
	resp.append(frame.data[1])
	resp.append(12) #SubFunctionNotSupported
	isotp_send(dev, resp, 3)

def send_error_roor(dev,frame,id):
	resp = []
	if(verbose):
		plog("Responded with Sub Function Not Supported\n")
	resp.append(0x7f)
	resp.append(frame.data[1])
	resp.append(31) # RequestOutOfRange
	isotp_send_to(dev, resp, 3, id)

def generic_OK_resp(dev,frame):
	resp = []
	if(verbose > 1):
		plog("Responding with a generic OK message\n")
	resp.append(frame.data[1] + 0x40)
	resp.append(frame.data[2])
	resp.append(0)
	isotp_send(dev, resp, 3)

def generic_OK_resp_to(dev, frame, id):
	resp = []
	if(verbose > 1):
		plog("Responding with a generic OK message\n")
	resp.append(frame.data[1] + 0x40)
	resp.append(frame.data[2])
	resp.append(0)
	isotp_send_to(dev, resp, 3, id)

def handle_current_data(dev,frame):
	if(verbose):
		plog("Received Current info request\n")
	if(frame.data[2] == 0x00): # Supported PIDs
		if(verbose):
			plog("Responding with a generic set of PIDs (1-20)\n")
		resp = [frame.data[1] + 0x40,frame.data[2],0xBF,0xBF,0xB9,0x93]
		#print resp
		isotp_send(dev, resp, 6)
	elif(frame.data[2] == 0x01): # MIL & DTC Status
		if(verbose):
			plog("Responding to MIL and DTC Status request\n")
		resp = [frame.data[1] + 0x40,frame.data[2],0x00,0x07,0xE5,0xE5]
		isotp_send(dev, resp, 6)
	elif(frame.data[2] == 0x20):# More supported PIDs (21-40)
		if(verbose):
			plog("Responding with PIDs supported (21-40)\n")
		resp = [frame.data[1] + 0x40,frame.data[2],0xBF,0xBF,0xB9,0x93]
		isotp_send(dev, resp, 6)
	elif(frame.data[2] == 0x40):#More supported PIDs (41-60)
		if(verbose):
			plog("Responding with PIDs supported (41-60)\n")
		resp = [frame.data[1] + 0x40,frame.data[2],0xBF,0xBF,0xB9,0x93]
		isotp_send(dev, resp, 6)
	elif(frame.data[2] == 0x41):#Monitor status this drive cycle
		resp = [frame.data[1] + 0x40,frame.data[2],0,0x0F,0xFF,0x00]
		isotp_send(dev, resp, 6)
	elif(frame.data[2] == 0x60):#More supported PIDs (61-80)
		if(verbose):
			plog("Responding with PIDs supported (61-80)\n")
		resp = [frame.data[1] + 0x40,frame.data[2],0xBF,0xBF,0xB9,0x93]
		isotp_send(dev, resp, 6)
	elif(frame.data[2] == 0x80):#More supported PIDs (81-100)
		if(verbose):
			plog("Responding with PIDs supported (81-100)\n")
		resp = [frame.data[1] + 0x40,frame.data[2],0xBF,0xBF,0xB9,0x93]
		isotp_send(dev, resp, 6)
	elif(frame.data[2] == 0xA0):# More Supported PIDs (101-120)
		if(verbose):
			plog("Responding with PIDs supported (101-120)\n")
		resp = [frame.data[1] + 0x40,frame.data[2],0xBF,0xBF,0xB9,0x93]
		isotp_send(dev, resp, 6)
	elif(frame.data[2] == 0xC0):#More supported PIDs (121-140)
		if(verbose):
			plog("Responding with PIDs supported (121-140)\n")
		resp = [frame.data[1] + 0x40,frame.data[2],0xBF,0xBF,0xB9,0x93]
		isotp_send(dev, resp, 6)
	else:
		if(verbose):
			log = "Note: Requested unsupported service %02X\n"%frame.data[2]
			plog(log)
def handle_vehicle_info(dev,frame):
	if(verbose):
		plog("Received Vehicle info request\n")
	if(frame.data[2] == 0x00): #Supported PIDs
		if(verbose):
			plog("Replying with ALL Pids supported\n")
		resp = [frame.data[1] + 0x40,frame.data[2],0x55,0,0,0]
		isotp_send(dev, resp, 6)
	elif(frame.data[2] == 0x02):#Get VIN
		if(fuzz_level == 0):			
			vin = VIN
			chksum = calc_vin_checksum(vin, 17)
			print vin
			vin = list(vin)
			#vin[8] = chksum
			resp = [frame.data[1] + 0x40,frame.data[2],1]
			
			if(verbose):
				log = "Sending VIN %s\n"%vin
				plog(log)

			for n in range(17):
				if type(vin[n]) == int:
					resp.append(vin[n])
				else:
					resp.append(ord(vin[n]))
			#resp[3:] = vin
			#resp[3:] = [0x56,0x49,0x53,0x55,0x41,0x4C,0x54,0x48,0x52,0x45,0x41,0x54]
			
			print resp
			isotp_send(dev, resp, 3 + len(vin))
		elif(fuzz_level == 1):
			if(verbose):
				plog("Fuzzing VIN with printable chars\n")
			resp = [frame.data[1] + 0x40,frame.data[2],1]
			buf = gen_data(DATA_ALPHANUM, 17)
			chksum = calc_vin_checksum(buf, 17)
			buf[8] = chksum
			if(verbose):
				log = "Using VIN: %s\n"%buf
				plog(log)
			for n in range(17):
				if type(buf[n]) == int:
					resp.append(buf[n])
				else:
					resp.append(ord(buf[n]))
			#resp[3:] = buf
			isotp_send(dev, resp, 4 + 17)
		elif(fuzz_level == 2 or fuzz_level == 3):#At 3 the ISOTP spec gets flaky
			pktsize = random.randint(0,251)
			if(verbose):
				plog("Fuzzing big VIN with printable chars\n")
			resp = [frame.data[1] + 0x40,frame.data[2],1]
			buf = gen_data(DATA_ALPHANUM, pktsize)
			chksum = calc_vin_checksum(buf, pktsize)
			#print "mark2"
			#print buf
			#print chksum
			#print pktsize
			if(len(buf)>8):
				buf[8] = chksum
			if(verbose):
				log = "Using big VIN (%d chars): %s\n"%(pktsize, buf)
				plog(log)
			for n in range(pktsize):

				if type(buf[n]) == int:
					resp.append(buf[n])
				else:
					resp.append(ord(buf[n]))	
			#resp[3:] = buf[0:pktsize]
			isotp_send(dev, resp, 4 + pktsize)
		elif(fuzz_level == 4):
			if(verbose):
				plog("Fuzzing VIN with binary data\n")
			resp = [frame.data[1] + 0x40,frame.data[2],1]
			buf = gen_data(DATA_BINARY, 17)
			chksum = calc_vin_checksum(buf, 17)
			buf[8] = chksum
			if(verbose):
				print_bin(buf, 17)
			for n in range(17):
				if type(buf[n]) == int:
					resp.append(buf[n])
				else:
					resp.append(ord(buf[n]))
			#resp[3:] = buf[0:17]
			isotp_send(dev, resp, 4 + 17)
		else:
			pktsize = random.randint(0,251)
			if(verbose):
				log ="Fuzzing VIN with binary data with size %d\n" %pktsize
				plog(log)
			resp = [frame.data[1] + 0x40,frame.data[2],1]
			buf = gen_data(DATA_BINARY, pktsize)
			if(verbose):
				print_bin(buf, pktsize)
			for n in range(pktsize):
				if type(buf[n]) == int:
					resp.append(buf[n])
				else:
					resp.append(ord(buf[n]))
			#resp[3:] = buf[0:pktsize]
			isotp_send(dev, resp, 4 + pktsize)

def handle_pending_codes(dev,frame):
	if(verbose):
		plog("Received request for pending trouble codes\n")
	send_dtcs(dev, 20, frame)

def handle_stored_codes(dev, frame):
	if(verbose):
		plog("Received request for stored trouble codes\n")
	send_dtcs(dev, 2, frame)

# TODO: This is wrong.  Record a real transaction to see the format
def handle_freeze_frame(dev, frame):
	if(verbose):
		plog("Received request for freeze frame code\n")
	#send_dtcs(can, 1, frame);
	resp = [frame.data[1] + 0x40,0x01,0x01]
	isotp_send(dev, resp, 3)

def handle_perm_codes(dev,frame):
	if(verbose):
		plog("Received request for permanent trouble codes\n")
	send_dtcs(dev, 0, frame)

def handle_dsc(dev,frame):
	#if(verbose) plog("Received DSC Request\n");
	#send_error_snfs(can, frame);
	if(verbose):
		plog("Received DSC Request giving VCDS respose\n")
	frame.id = 0x77A
	frame.len = 8
	frame.data = [0x06,0x50,0x03,0x00,0x32,0x01,0xF4,0xAA]
	dev.send_driver(frame)
	logdataobj.append(frame)

#ECU Memory, based on VCDS response for now
def handle_read_data_by_id(dev,frame):
	if(verbose):
		log = "Recieved Read Data by ID %02X %02X\n"%(frame.data[2], frame.data[3])
		plog(log)
	if(frame.data[2] == 0xF1):
		if(frame.data[3] == 0x87):
			if(verbose):
				plog("Read data by ID 0x87\n")
			resp = [frame.data[1] + 0x40,frame.data[2],0x87,0x30,0x34,0x45,0x39,0x30,0x36,0x33,0x32,0x33,0x46,0x20]
			isotp_send_to(dev, resp, 14, 0x77A)
		elif(frame.data[3] == 0x89):
			if(verbose):
				plog("Read data by ID 0x89\n")
			frame.id = 0x7E8;
			frame.len = 8;
			frame.data = [0x07,0x62,0xF1,0x89,0x38,0x34,0x31,0x30]
			dev.send_driver(frame)
		elif(frame.data[3] == 0x9E):
			if(verbose):
				plog("Read data by ID 0x9E\n")
			resp = [frame.data[1] + 0x40,frame.data[2],0x45,0x56,0x5F,0x47,0x61,0x74,0x65,0x77,0x45,0x56,0x43,0x6F,0x6E,0x74,0x69,0x00]
			isotp_send(dev, resp, 0x13)
		elif(frame.data[3] == 0xA2):
			if(verbose):
				plog("Read data by ID 0xA2\n")
			resp = [frame.data[1] + 0x40,frame.data[2],0xA2,0x30,0x30,0x34,0x30,0x31,0x30]
			isotp_send(dev, resp, 9)
		else:
			if(verbose):
				log = "Not responding to ID %02X\n"%frame.data[3]
				plog(log)
	elif(frame.data[2] == 0x06):
		if(frame.data[3] == 0x00):
			if(verbose):
				plog("Read data by ID 0x9E\n")
			resp = []
			resp.append(frame.data[1] + 0x40)
			resp.append(frame.data[2])
			resp.append(0x02)
			resp.append(0x01)
			resp.append(0x00)
			resp.append(0x17)
			resp.append(0x26)
			resp.append(0xF2)
			resp.append(0x00)
			resp.append(0x00)
			resp.append(0x5B)
			resp.append(0x00)
			resp.append(0x12)
			resp.append(0x08)
			resp.append(0x58)
			resp.append(0x00)
			resp.append(0x00)
			resp.append(0x00)
			resp.append(0x00)
			resp.append(0x01)
			resp.append(0x01)
			resp.append(0x01)
			resp.append(0x00)
			resp.append(0x01)
			resp.append(0x00)
			resp.append(0x00)
			resp.append(0x00)
			resp.append(0x00)
			resp.append(0x00)
			resp.append(0x00)
			resp.append(0x00)
			resp.append(0x00)
			isotp_send(dev, resp, 0x21)
		elif(frame.data[3] == 0x01):
			if(verbose):
				plog("Read data by ID 0x01\n")
			send_error_roor(dev, frame, 0x7E8)
		else:
			if(verbose):
				log = "Not responding to ID %02X\n"%frame.data[3] 
				plog(log)
	else:
		if(verbose):
			log = "Unknown read data by ID %02X\n" %frame.data[2] 
			plog(log)

# Read DID from ID (GM)
# For now we are only setting this up to work with the BCM
# 244   [3]  02 1A 90
def handle_gm_read_did_by_id(dev, frame):
	if(verbose):
		plog("Received GM Read DID by ID Request\n")
	tracenum = "874602RA51950204"
	if(frame.data[2] == 0x90): # VIN
		if(verbose):
			plog(" + Requested VIN\n")
		if(fuzz_level == 0):
			if(verbose):
				log = "Sending VIN %s\n"%vin 
				plog(log)
			resp = [frame.data[1] + 0x40,frame.data[2]]
			resp[2:] = vin
			isotp_send_to(dev, resp, 3 + len(vin), 0x644)
		elif(fuzz_level == 1):
			if(verbose):
				plog("Fuzzing VIN with printable chars\n")
			resp = [frame.data[1] + 0x40,frame.data[2]]
			buf = gen_data(DATA_ALPHANUM, 17)
			chksum = calc_vin_checksum(buf, 17);
			buf[8] = chksum
			if(verbose):
				log = "Using VIN: %s\n" %buf 
				plog(log)
			resp[2:] = buf[0:17]
			isotp_send_to(dev, resp, 3 + 17, 0x644)
		elif(fuzz_level == 2 or fuzz_level == 3):
			pktsize = random.randint(0,251)
			if(verbose):
				plog("Fuzzing big VIN with printable chars\n")
			resp = [frame.data[1] + 0x40,frame.data[2]]
			buf = gen_data(DATA_ALPHANUM, pktsize)
			chksum = calc_vin_checksum(buf, pktsize)
			if(pktsize > 8):
          			buf[8] = chksum
			if(verbose):
				log = "Using big VIN (%d chars): %s\n"%(pktsize, buf) 
				plog(log)
			resp[2:] = buf[0:pktsize]
			isotp_send_to(dev, resp, 3 + pktsize, 0x644)
		elif(fuzz_level == 4):
			if(verbose):
				plog("Fuzzing VIN with binary data\n")
			resp = [frame.data[1] + 0x40,frame.data[2]]
			buf = gen_data(DATA_BINARY, 17)
			chksum = calc_vin_checksum(buf, 17)
			buf[8] = chksum
			if(verbose):
				print_bin(buf, 17)
			resp[2:] = buf[0:17]
			isotp_send_to(dev, resp, 3 + 17, 0x644)
		else:
			pktsize = random.randint(0,251)
			if(verbose):
				log = "Fuzzing VIN with binary data with size %d\n"%pktsize
				plog(log)
			resp = [frame.data[1] + 0x40,frame.data[2]]
			buf = gen_data(DATA_BINARY, pktsize)
			if(verbose):
				print_bin(buf, pktsize)
			resp[2:] = buf[0:pktsize]
			isotp_send_to(dev, resp, 3 + pktsize, 0x644)
	elif(frame.data[2] == 0xA1):# SDM Primary Key
		if(verbose):
			plog(" + Requested SDM Primary Key\n")
		if(verbose):
			plog("Sending SDM Key 0x6966\n")
		resp = [frame.data[1] + 0x40,frame.data[2],0x69,0x66]
		isotp_send_to(dev, resp, 5, 0x644)
	elif(frame.data[2] == 0xB4):# Traceability Number
		if(verbose):
			plog(" + Requested Traceability Number\n")
		if(verbose):
			log = "Sending Traceabiliity number %s\n"%tracenum
			plog(log)
		resp = [frame.data[1] + 0x40,frame.data[2]]
		resp[2:] = tracenum
		isotp_send_to(dev, resp, 3 + len(tracenum), 0x644)
	elif(frame.data[2] == 0xB7): #Software Number
		if(verbose):
			plog(" + Requested Software Number\n")
		if(verbose):
			plog("Sending SW # 600\n")
		resp = [frame.data[1] + 0x40,frame.data[2],0x42,0xAA,6,2,0x58]
		isotp_send_to(dev, resp, 6, 0x644)
	elif(frame.data[2] == 0xCB): #End Model Part #
		if(verbose):
			plog(" + Requested End Model Part Number\n")
		if(verbose):
			plog("Sending End Model Part Number 15804602\n")
		resp = [frame.data[1] + 0x40,frame.data[2],0x00,0xF1,0x28,0xBA]
		isotp_send_to(dev, resp, 6, 0x644)

# GM Read Data via PID */
# 244   [5]  04 AA 03 02 07 */
# 544#0738408D8B000200 */
# 544#02508D8D00000000 */
def handle_gm_read_data_by_id(dev,frame):
	if(verbose):
		plog("Received GM Read Data by ID Request\n")
	offset = 0
	datacpy = []
	if (frame.data[0] == 0xFE):
		offset = 1
	datacpy = frame.data[0:8]
	if(frame.id == 0x7e0):
    		frame.id = 0x5e8
	else:
		frame.id = 0x500 + (frame.id & 0xFF)
	frame.len = 8
	if(frame.data[2 + offset] == 0x00):# Stop
		if(verbose):
			plog(" + Stop Data Request\n")
		frame.data = [0,0,0,0,0,0,0,0]
		dev.send_driver(frame)
		logdataobj.append(frame)
		CONST.CLEAR_BIT(pending_data, CONST.PENDING_READ_DATA_BY_ID_GM)
	elif(frame.data[2 + offset] == 0x01): # One Response
		if(verbose):
			plog(" + One Response\n")
		for i in range(3,datacpy[0]+1):
			frame.data[0] = datacpy[i]
			for datacnt in range(1,8):
				frame.data[datacnt] = random.randint(0,255)
			dev.send_driver(frame)
			logdataobj.append(frame)
			time.sleep(0.5)
	elif(frame.data[2 + offset] == 0x02): #Slow Rate
		if(verbose):
			plog(" + Slow Rate\n")
		CONST.SET_BIT(pending_data, CONST.PENDING_READ_DATA_BY_ID_GM)
		gm_data_by_id = frame
	elif(frame.data[2 + offset] == 0x03): #Medium Rate
		if(verbose):
			plog(" + Medium Rate\n")
		CONST.SET_BIT(pending_data, CONST.PENDING_READ_DATA_BY_ID_GM)
		gm_data_by_id = frame
	elif(frame.data[2 + offset] == 0x04): #Fast Rate
		if(verbose):
			plog(" + Fast Rate\n")
		CONST.SET_BIT(pending_data, CONST.PENDING_READ_DATA_BY_ID_GM)
		gm_data_by_id = frame
	else:
		plog("Unknown subfunction timer\n")

# GM Diag format is either
#     101#FE 03 A9 81 52  (Functional addressing: Where FE is the extended address)
#     7E0#03 A9 81 52 (no extended addressing)
#
def handle_gm_read_diag(dev,frame):
	if(verbose):
		plog("Received GM Read Diagnostic Request\n")
	offset = 0
	if(frame.data[0] == 0xFE):
		offset = 1
	if(frame.data[2 + offset] == CONST.UDS_READ_STATUS_BY_MASK):
		if(verbose):
			plog(" + Read DTCs by mask\n")
			if(frame.data[3 + offset] & CONST.DTC_SUPPORTED_BY_CALIBRATION):
				plog("   - Supported By Calibration\n")
			if(frame.data[3 + offset] & CONST.DTC_CURRENT_DTC):
				plog("   - Current DTC\n")
			if(frame.data[3 + offset] & CONST.DTC_TEST_NOT_PASSED_SINCE_CLEARED):
				plog("   - Tests not passed since DTC cleared\n")
			if(frame.data[3 + offset] & CONST.DTC_TEST_FAILED_SINCE_CLEARED):
				plog("   - Tests failed since DTC cleared\n")
			if(frame.data[3 + offset] & CONST.DTC_HISTORY):
				plog("   - DTC History\n")
			if(frame.data[3 + offset] & CONST.DTC_TEST_NOT_PASSED_SINCE_POWER):
				plog("   - Tests not passed since power up\n")
			if(frame.data[3 + offset] & CONST.DTC_CURRENT_DTC_SINCE_POWER):
				plog("   - Tests failed since power up\n")
			if(frame.data[3 + offset] & CONST.DTC_WARNING_INDICATOR_STATE):
				plog("   - Warning Indicator State\n")
		if(frame.id == 0x7e0):
			frame.id = 0x5e8
		else:
			frame.id = 0x500 + (frame.id & 0xFF)
		frame.len = 8
		frame.data = [frame.data[2 + offset],0,0x30,0,0x6F,0,0,0]
		dev.send_driver(frame)
		logdataobj.append(frame)
		time.sleep(0.2); # Instead of actually processing the FC
		if(fuzz_level == 1):
			total = random.randint(0,1023)
			if(verbose):
				log = "Sending %d DTCs\n" %total 
				plog(log)
			for i in range(0,total):
				frame.data[1] = random.randint(0,255)
				frame.data[2] = (random.randint(0,254)) + 1
				frame.data[3] = 0
				frame.data[4] = 0x6F # Last DTC
				dev.send_driver(frame)
				logdataobj.append(frame)
				time.sleep(1)
		frame.data[1] = 0 # Last frame must be a 0 DTC
		frame.data[2] = 0
		frame.data[3] = 0
		frame.data[4] = 0xFF # Last DTC
		dev.send_driver(frame)
		logdataobj.append(frame)
	else:
		if(verbose):
			log = " + Unknown subfunction request %02X\n" %frame.data[2 + offset]
			plog(log)

#
#  Gateway
#
def handle_vcds_710(dev,frame):
	if(verbose):
		plog("Received VCDS 0x710 gateway request\n")
	if(frame.data[0] == 0x30): # Flow control
		flow_control_push(dev)
		return
	if(frame.data[1] == 0x10): #Diagnostic Session Control
    	#Pkt: 710#02 10 03 55 55 55 55 55
		frame.id = 0x77A
		frame.len = 8;
		frame.data = [0x06,0x50,0x03,0x00,0x32,0x01,0xF4,0xAA]
		dev.send_driver(frame)
		logdataobj.append(frame)
	elif(frame.data[1] == 0x22):# Read Data By Identifier
		if(frame.data[2] == 0xF1):
			if(frame.data[3] == 0x87): #VAG Number
				if(verbose):
					plog("Read data by ID 0x87\n")
				resp.append(frame.data[1] + 0x40)
				resp.append(frame.data[2])
				resp.append(0x87)
				resp.append(0x35)
				resp.append(0x51)
				resp.append(0x45)
				resp.append(0x39)
				resp.append(0x30)
				resp.append(0x37)
				resp.append(0x35)
				resp.append(0x33)
				resp.append(0x30)
				resp.append(0x43)
				resp.append(0x20) # Note normally this would pad with AA's
				isotp_send_to(dev, resp, 14, 0x77A)
			elif(frame.data[3] == 0x89):# VAG Number
				if(verbose):
					plog("Read data by ID 0x89\n")
				frame.id = 0x77A
				frame.len = 8
				frame.append(0x07)
				frame.data[1] = 0x62
				frame.data[2] = 0xF1
				frame.data[3] = 0x89
				frame.data[4] = 0x33 #3
				frame.data[5] = 0x32 #2
				frame.data[6] = 0x30 #0
				frame.data[7] = 0x33 #3
				dev.send_driver(frame)
				logdataobj.append(frame)
			elif(frame.data[3] == 0x91): #VAG Number
				if(verbose):
					plog("Read data by ID 0x91\n")
				resp.append(frame.data[1] + 0x40)
				resp.append(frame.data[2])
				resp.append(0x87)
				resp.append(0x35)
				resp.append(0x51)
				resp.append(0x45)
				resp.append(0x39)
				resp.append(0x30)
				resp.append(0x37)
				resp.append(0x35)
				resp.append(0x33)
				resp.append(0x30)
				resp.append(0x41)
				resp.append(0x20)# Note normally this would pad with AA's
				isotp_send_to(dev, resp, 14, 0x77A)
			else:
				if(verbose):
					log = "NOTE: Read data by unknown ID %02X\n"%frame.data[3] 
					plog(log)
				resp.append(frame.data[1] + 0x40)
				resp.append(frame.data[2])
				resp.append(0x87)
				resp.append(0x35)
				resp.append(0x51)
				resp.append(0x45)
				resp.append(0x39)
				resp.append(0x30)
				resp.append(0x37)
				resp.append(0x35)
				resp.append(0x33)
				resp.append(0x30)
				resp.append(0x41)
				resp.append(0x20) # Note normally this would pad with AA's
				isotp_send_to(dev, resp, 14, 0x77A)
		else:
			if (verbose):
				log = "Unknown read data by Identifier %02X\n" %frame.data[2] 
				plog(log)

# return Mode/SIDs in english
def get_mode_str(frame):
	if(frame.data[1] == CONST.OBD_MODE_SHOW_CURRENT_DATA):
		return "Show current Data"
	elif(frame.data[1] == CONST.OBD_MODE_SHOW_FREEZE_FRAME):
		return "Show freeze frame"
	elif(frame.data[1] == CONST.OBD_MODE_READ_DTC):
		return "Read DTCs"
	elif(frame.data[1] == CONST.OBD_MODE_CLEAR_DTC):
		return "Clear DTCs"
	elif(frame.data[1] == CONST.OBD_MODE_TEST_RESULTS_NON_CAN):
       		return "Mode Test Results (Non-CAN)"
	elif(frame.data[1] == CONST.OBD_MODE_TEST_RESULTS_CAN):
       		return "Mode Test Results (CAN)"
	elif(frame.data[1] == CONST.OBD_MODE_READ_PENDING_DTC):
       		return "Read Pending DTCs"
	elif(frame.data[1] == CONST.OBD_MODE_CONTROL_OPERATIONS):
       		return "Control Operations"
	elif(frame.data[1] == CONST.OBD_MODE_VEHICLE_INFORMATION):
       		return "Vehicle Information"
	elif(frame.data[1] == CONST.OBD_MODE_READ_PERM_DTC):
       		return "Read Permanent DTCs"
	elif(frame.data[1] == CONST.UDS_SID_DIAGNOSTIC_CONTROL):
       		return "Diagnostic Control"
	elif(frame.data[1] == CONST.UDS_SID_ECU_RESET):
       		return "ECU Reset"
	elif(frame.data[1] == CONST.UDS_SID_CLEAR_DTC):
       		return "UDS Clear DTCs"
	elif(frame.data[1] == CONST.UDS_SID_READ_DTC):
       		return "UDS Read DTCs"
	elif(frame.data[1] == CONST.UDS_SID_GM_READ_DID_BY_ID):
       		return "Read DID by ID (GM)"
	elif(frame.data[1] == CONST.UDS_SID_RESTART_COMMUNICATIONS):
       		return "Restore Normal Commnications"
	elif(frame.data[1] == CONST.UDS_SID_READ_DATA_BY_ID):
       		return "Read DATA By ID"
	elif(frame.data[1] == CONST.UDS_SID_READ_MEM_BY_ADDRESS):
       		return "Read Memory By Address"
	elif(frame.data[1] == CONST.UDS_SID_READ_SCALING_BY_ID):
       		return "Read Scalling Data by ID"
	elif(frame.data[1] == CONST.UDS_SID_SECURITY_ACCESS):
       		return "Security Access"
	elif(frame.data[1] == CONST.UDS_SID_COMMUNICATION_CONTROL):
       		return "Communication Control"
	elif(frame.data[1] == CONST.UDS_SID_READ_DATA_BY_ID_PERIODIC):
       		return "Read DATA By ID Periodically"
	elif(frame.data[1] == CONST.UDS_SID_DEFINE_DATA_ID):
       		return "Define DATA By ID"
	elif(frame.data[1] == CONST.UDS_SID_WRITE_DATA_BY_ID):
       		return "Write DATA By ID"
	elif(frame.data[1] == CONST.UDS_SID_IO_CONTROL_BY_ID):
       		return "Input/Output Control By ID"
	elif(frame.data[1] == CONST.UDS_SID_ROUTINE_CONTROL):
       		return "Routine Control"
	elif(frame.data[1] == CONST.UDS_SID_REQUEST_DOWNLOAD):
       		return "Request Download"
	elif(frame.data[1] == CONST.UDS_SID_REQUEST_UPLOAD):
       		return "Request Upload"
	elif(frame.data[1] == CONST.UDS_SID_TRANSFER_DATA):
       		return "Transfer DATA"
	elif(frame.data[1] == CONST.UDS_SID_REQUEST_XFER_EXIT):
       		return "Request Transfer Exit"
	elif(frame.data[1] == CONST.UDS_SID_REQUEST_XFER_FILE):
       		return "Request Transfer File"
	elif(frame.data[1] == CONST.UDS_SID_WRITE_MEM_BY_ADDRESS):
       		return "Write Memory By Address"
	elif(frame.data[1] == CONST.UDS_SID_TESTER_PRESENT):
       		return "Tester Present";
	elif(frame.data[1] == CONST.UDS_SID_ACCESS_TIMING):
       		return "Access Timing"
	elif(frame.data[1] == CONST.UDS_SID_SECURED_DATA_TRANS):
       		return "Secured DATA Transfer"
	elif(frame.data[1] == CONST.UDS_SID_CONTROL_DTC_SETTINGS):
       		return "Control DTC Settings"
	elif(frame.data[1] == CONST.UDS_SID_RESPONSE_ON_EVENT):
       		return "Response On Event"
	elif(frame.data[1] == CONST.UDS_SID_LINK_CONTROL):
       		return "Link Control"
	elif(frame.data[1] == CONST.UDS_SID_GM_PROGRAMMED_STATE):
       		return "Programmed State (GM)"
	elif(frame.data[1] == CONST.UDS_SID_GM_PROGRAMMING_MODE):
       		return "Programming Mode (GM)"
	elif(frame.data[1] == CONST.UDS_SID_GM_READ_DIAG_INFO):
       		return "Read Diagnostic Information (GM)"
	elif(frame.data[1] == CONST.UDS_SID_GM_READ_DATA_BY_ID):
       		return "Read DATA By ID (GM)"
	elif(frame.data[1] == CONST.UDS_SID_GM_DEVICE_CONTROL):
       		return "Device Control (GM)"
	else:
       		printf("Unknown mode/sid (%02X)\n" %frame.data[1])

# Handles the incomming CAN Packets
# Each ID that deals with specific controllers a note is
# given where that info came from.  There could be a lot of overlap
# and exceptions here. -- Craig
def handle_pkt(dev,frame):
	if(DEBUG):
		print_pkt(frame)
	if(frame.id == 0x243):
		# EBCM / GM / Chevy Malibu 2006
		if(frame.data[1] == CONST.UDS_SID_TESTER_PRESENT):
			if(verbose > 1):
				plog("Received TesterPresent\n")
			generic_OK_resp_to(dev, frame, 0x643)
		elif(frame.data[1] == CONST.UDS_SID_GM_READ_DIAG_INFO):
			handle_gm_read_diag(dev, frame)
		else:
			if(verbose):
				print_pkt(frame)
		if(verbose):
			log = "Unhandled mode/sid: %s\n" %get_mode_str(frame) 
			plog(log)
	elif(frame.id == 0x244):# Body Control Module / GM / Chevy Malibu 2006
		if(frame.data[0] == 0x30): # Flow control
			flow_control_push_to(dev, 0x644)
		if(frame.data[1] == CONST.UDS_SID_TESTER_PRESENT):
			if(verbose > 1):
				plog("Received TesterPresent\n")
			generic_OK_resp_to(dev, frame, 0x644)
		elif(frame.data[1] == CONST.UDS_SID_GM_READ_DIAG_INFO):
			handle_gm_read_diag(dev, frame)
		elif(frame.data[1] == CONST.UDS_SID_GM_READ_DATA_BY_ID):
			handle_gm_read_data_by_id(dev, frame)
		elif(frame.data[1] == CONST.UDS_SID_GM_READ_DID_BY_ID):
			handle_gm_read_did_by_id(dev, frame)
		else:
			if(verbose):
				print_pkt(frame)
			if(verbose):
				log = "Unhandled mode/sid: %s\n"%get_mode_str(frame) 
				plog(log)
	elif(frame.id == 0x24A): #// Power Steering / GM / Chevy Malibu 2006
		if(verbose):
			print_pkt(frame);
		if(verbose):
			log = "Unhandled mode/sid: %s\n" %get_mode_str(frame) 
			plog(log)
	elif(frame.id == 0x350): #// Unsure.  Seen RTRs to this when requesting VIN
		if (frame.id and CONST.CAN_RTR_FLAG):
			if (verbose):
				log = "Received a RTR at ID %02X\n" %frame.id
				plog(log)
	elif(frame.id == 0x710): #// VCDS
		if(verbose):
			print_pkt(frame)
		handle_vcds_710(dev, frame)
	elif(frame.id == 0x7df or frame.id == 0x7e0):#// Sometimes flow control comes here
		if(verbose):
			print_pkt(frame)
		if(frame.data[0] == 0x30 and gBufLengthRemaining > 0):
			flow_control_push(dev)
		if(frame.data[0] == 0 or frame.get_len() == 0):
			return
		if(frame.data[0] > frame.get_len()):
			return
		if(frame.data[1] == CONST.OBD_MODE_SHOW_CURRENT_DATA):
          		handle_current_data(dev, frame);
		elif(frame.data[1] == CONST.OBD_MODE_SHOW_FREEZE_FRAME):
          		handle_freeze_frame(dev, frame);
		elif(frame.data[1] == CONST.OBD_MODE_READ_DTC):
          		handle_stored_codes(dev, frame);
		elif(frame.data[1] == CONST.OBD_MODE_READ_PENDING_DTC):
          		handle_pending_codes(dev, frame);
		elif(frame.data[1] == CONST.OBD_MODE_VEHICLE_INFORMATION):
          		handle_vehicle_info(dev, frame)
		elif(frame.data[1] == CONST.OBD_MODE_READ_PERM_DTC):
          		handle_perm_codes(dev, frame)
		elif(frame.data[1] == CONST.UDS_SID_DIAGNOSTIC_CONTROL):
          		handle_dsc(dev, frame)
		elif(frame.data[1] == CONST.UDS_SID_READ_DATA_BY_ID):
        		handle_read_data_by_id(dev, frame)
		elif(frame.data[1] == CONST.UDS_SID_TESTER_PRESENT):
			if(verbose > 1):
				plog("Received TesterPresent\n")
			generic_OK_resp(dev, frame)
		elif(frame.data[1] == CONST.UDS_SID_GM_READ_DIAG_INFO):
          		handle_gm_read_diag(dev, frame)
		else:
          		#if(verbose) plog("Unhandled mode/sid: %02X\n", frame.data[1]);
			if(verbose):
				log = "Unhandled mode/sid: %s\n"%get_mode_str(frame) 
				plog(log)
	else:
		if (DEBUG):
			print_pkt(frame)
		if (DEBUG):
			log = "DEBUG: missed ID %02X\n" %frame.id 
			plog(log)

if __name__ == "__main__":
	can_name = None
	print "sudo python udsspoof.py candev baudrate"
	try:
		opts, args = getopt.getopt(sys.argv[1:], "cV:zl:vFh", ["help="])
		if (len(args) < 1):
			usage(sys.argv[0], "You must specify at least one can device")
		else:
			can_name = args[len(args)-2]
			print ("can name: %s"%can_name)		

	except getopt.GetoptError as err:
        	# print help information and exit:
		print (str(err))  # will print something like "option -a not recognized"
		usage(can_name,None)
		sys.exit(2)
	for o, a in opts:
		if o == "-c":
			keep_spec = 1
		elif o == "-v":
			verbose = verbose + 1
		elif o == "-V":
			vin = a
		elif o == "-F":
			no_flow_control = 1
		elif o == "-z":
			fuzz_level = fuzz_level + 1
		elif o == "-h":
			usage(sys.argv[0],None)
		else:
			usage(sys.argv[0],None)

	timeout = 1.02 #20ms
	#dev = CantactDev(sys.argv[1],timeout)
	dev = CANDriver(can_name,int(sys.argv[2]))
	dev.operate(Operate.START)

	start_tv = time.time()
	frame = None


	data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
	frame = CAN_Packet()
	frame.configure(0x7dd,0x8,data)

	dev.send_driver(frame)
	count = 0

	VTlogfile = CANSocket()

	while((time.time()-start_tv) < 3*60):
		print count
		count += 1		
		frame = dev.receive_driver()
		logdataobj.append(frame)
		handle_pkt(dev, frame)
		handle_pending_data(dev)
		time.sleep(0.1)		

	
	logname = VTlogfile.logfrarray2file(VTlogfile,logdataobj,"P","Log Frames")
	print "Finish the program!"
	print logname

