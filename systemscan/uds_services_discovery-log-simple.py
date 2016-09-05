import sys
sys.path.append("..")
from CanLib.CAN_protocol import *
from CanLib.CAN_Packet import * 
from CanLib.CAN_Driver import *
from CanLib.vtlog import *
from reversing import autoscan
import random
import math
import time
from sys import stdout
import argparse
import os


# This program is to scan system automatically and find dst,Services,Subfunctions.
# sudo python uds-services-discovery.py /dev/ttyACM0 125000 0.5
# payloads: 125000(baudrate),0.5(timeout 0.5 second)

SERVICE_NAMES = {
    0x10: 'DIAGNOSTIC_SESSION_CONTROL',
    0x11: 'ECU_RESET',
    0x12: 'GMLAN_READ_FAILURE_RECORD',
    0x14: 'CLEAR_DIAGNOSTIC_INFORMATION',
    0x19: 'READ_DTC_INFORMATION',
    0x1A: 'GMLAN_READ_DIAGNOSTIC_ID',
    0x20: 'RETURN_TO_NORMAL',
    0x22: 'READ_DATA_BY_IDENTIFIER',
    0x23: 'READ_MEMORY_BY_ADDRESS',
    0x24: 'READ_SCALING_DATA_BY_IDENTIFIER',
    0x27: 'SECURITY_ACCESS',
    0x28: 'COMMUNICATION_CONTROL',
    0x2A: 'READ_DATA_BY_PERIODIC_IDENTIFIER',
    0x2C: 'DYNAMICALLY_DEFINE_DATA_IDENTIFIER',
    0x2D: 'DEFINE_PID_BY_MEMORY_ADDRESS',
    0x2E: 'WRITE_DATA_BY_IDENTIFIER',
    0x2F: 'INPUT_OUTPUT_CONTROL_BY_IDENTIFIER',
    0x31: 'ROUTINE_CONTROL',
    0x34: 'REQUEST_DOWNLOAD',
    0x35: 'REQUEST_UPLOAD',
    0x36: 'TRANSFER_DATA',
    0x37: 'REQUEST_TRANSFER_EXIT',
    0x38: 'REQUEST_FILE_TRANSFER',
    0x3B: 'GMLAN_WRITE_DID',
    0x3D: 'WRITE_MEMORY_BY_ADDRESS',
    0x3E: 'TESTER_PRESENT',
    0x7F: 'NEGATIVE_RESPONSE',
    0x83: 'ACCESS_TIMING_PARAMETER',
    0x84: 'SECURED_DATA_TRANSMISSION',
    0x85: 'CONTROL_DTC_SETTING',
    0x86: 'RESPONSE_ON_EVENT',
    0x87: 'LINK_CONTROL',
    0xA2: 'GMLAN_REPORT_PROGRAMMING_STATE',
    0xA5: 'GMLAN_ENTER_PROGRAMMING_MODE',
    0xA9: 'GMLAN_CHECK_CODES',
    0xAA: 'GMLAN_READ_DPID',
    0xAE: 'GMLAN_DEVICE_CONTROL'
}


NRC = {
    0x10: 'generalReject',
    0x11: 'serviceNotSupported',
    0x12: 'sub-functionNotSupported',
    0x13: 'incorrectMessageLengthOrInvalidFormat',
    0x14: 'responseTooBig',
    0x21: 'busyRepeatRequest',
    0x22: 'conditionsNotCorrect',
    0x24: 'requestSequenceError',
    0x25: 'noResponseFromSub-netComponent',
    0x26: 'failurePreventsExecutionOfRequestedAction',
    0x31: 'requestOutOfRange',
    0x33: 'securityAccessDenied',
    0x35: 'invalidKey',
    0x36: 'exceededNumberOfAttempts',
    0x37: 'requiredTimeDelayNotExpired',
    0x70: 'uploadDownloadNotAccepted',
    0x71: 'transferDataSuspended',
    0x72: 'generalProgrammingFailure',
    0x73: 'wrongBlockSequenceCounter',
    0x78: 'requestCorrectlyReceivedResponsePending',
    0x7E: 'sub-FunctionNotSupportedInActiveSession',
    0x7F: 'serviceNotSupportedInActiveSession'
}


def discoverdst(dev,timeout=1):

#============UDS dst ID discovery================================

	print "Start discovering dst ID..."
	
	found_ids = []	
	vtmsgbuffer = []
	VTlogfile = VTlog()
	dsts = []
	#/// comments
	vtmsgbuffer,found_ids = autoscan.collectAllID(dev,3)
	
	fr = CAN_Packet()
	#/// explain the payload the corresponding service type		0x02 means valid data of this frame. 0x10 means Diagnostics Section Control services. 0x01:Enter Default Section	
	fr.configure(0x00,8,[0x02, 0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
	
	devq = ISOTP_driver(dev)
	devq.operate(Operate.START)
	count = 0

	#/// why choose 1800???  should start from 0 to 2048. for saving time, start from 1800 to test. Meanwhile, uds ID always greater than 0x700
	for i in range(1800,2048):  # should start from 0 to 2048. for saving time, start from 1800 to test. Meanwhile, uds ID always greater than 0x700
		fr.id = i		
		if fr.id == 0x7df:		 #try 5 times, but if id=0x7df,set to 100
			looplen = 100
		else:
			looplen = 5
		
		vtmsg = VTMessage(fr.id,8,fr.get_payload(),1,0.01,"S","scan dst ID")
		vtmsgbuffer.append(vtmsg)

		print fr
		devq.send_packet(fr)

		for j in range(0,looplen): #try 5 times, but if id=0x7df,set to 100
			recvfr,flag = devq.get_packet_filter_array(timeout,found_ids)  #wait for response 2 seconds  only receive frames that not in found_ids						
			if recvfr != None:
				print recvfr
				vtmsg = VTMessage(recvfr.id,8,recvfr.get_payload(),1,0.01,"R","Recieve Frame")
				vtmsgbuffer.append(vtmsg)
				#/// why 0x50-7F???    0x50 and 0x7F
				if recvfr.get_payload()[1] in [0x50,0x7F]:
					count = count + 1
					dsts.append([i,recvfr.id])
					print "==================================="
					commentstr = str(count)+": Request CAN ID is 0x"+str(hex(i))+"; Resp dst ID is 0x"+str(hex(recvfr.id))
					print("%d: Request CAN ID is 0x%X; Resp dst ID is 0x%X" % (count,i,recvfr.id))
					print "==================================="
					vtmsgbuffer[-1]= VTMessage(recvfr.id,8,recvfr.get_payload(),1,0.01,"K",commentstr)
					if fr.id != 0x7df:
						break
			else:
				break
	logname = VTlogfile.writelog(vtmsgbuffer)
	print "\n\n============================================================="
	print("\nlog file: %s" % (logname))
	print "\n\n============================================================="
	print "Services id scan finished!"
	print "\n\n============================================================="

#=====finished, dst are stored in dsts data & file, count is number of dst===============
	devq.operate(Operate.STOP)
	return dsts

def discoverservices(dev,dsts=[],timeout=1):  # Scans for supported DCM services

	print("Starting discovering supported services")
	print dsts
	if dsts == None:
		return None
	#/// explain???	Init byte0 as valid length of the frame, byte1 and byte2 will get value in the below
	datatemp = [0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
	fr = CAN_Packet()
	fr.configure(0x00,8,datatemp)

	vtmsgbuffer = []
	VTlogfile = VTlog()	

	devq = ISOTP_driver(dev)
	devq.operate(Operate.START)
	count = 0
	supported_services = []
	#/// make comments below???  
	for i in range(0,len(dsts)):		#scan services for each dst we found before
		for j in range (0,256):			  #traverse byte1 that present services num
			fr.id = dsts[i][0]					# request ID
			datatemp[1]=j
			fr.data = datatemp

			devstatusflag = True
			while devstatusflag:			
				devq.send_packet(fr)
				print fr		
				vtmsg = VTMessage(fr.id,8,fr.get_payload(),1,0.01,"S","scan dst ID")
				vtmsgbuffer.append(vtmsg)

				recvfr,devstatusflag = devq.get_packet(timeout, filter=dsts[i][1])	# only receive frames by dst 
				#print "debug mark"
				
				

				if devstatusflag:
					devstatusflag = False
				else:
					devstatusflag = True

				if recvfr != None:
					print recvfr
					vtmsg = VTMessage(recvfr.id,8,recvfr.get_payload(),1,0.01,"R","Recieve Frame")
					vtmsgbuffer.append(vtmsg)
					if recvfr.get_payload()[3] not in [0x11]:	#0x11 means services not support
						count = count + 1
						supported_services.append([dsts[i][0],dsts[i][1],j]) #record the frame. dsts[i][0] means request id, dst[i][1] means related dst, j means supported services     
						service_name = SERVICE_NAMES.get(fr.get_payload()[1], "Unknown service") #print the services on the screen
						print "==================================="
				
						if recvfr.get_payload()[3] in [0x33,0x35,0x7E,0x7F]:  # 0x33: 'securityAccessDenied',0x35: 'invalidKey',0x7E: 'sub-FunctionNotSupportedInActiveSession',0x7F:'serviceNotSupportedInActiveSession'
							print("%d: %s 0x%X 0x%X %s" % (count,"Supported Services in high security level:",fr.id,fr.get_payload()[1],service_name))
							print "==================================="
							vtmsgbuffer[-1]= VTMessage(recvfr.id,8,recvfr.get_payload(),1,0.01,"K",service_name)
						else:
							print("%d: %s 0x%X 0x%X %s" % (count,"Supported Services:",fr.id,fr.get_payload()[1],service_name))
							print "==================================="
							vtmsgbuffer[-1]= VTMessage(recvfr.id,8,recvfr.get_payload(),1,0.01,"K",service_name)
	logname = VTlogfile.writelog(vtmsgbuffer)
	print "\n\n============================================================="
	print("\nlog file: %s" % (logname))		
	print "\n\n============================================================="
	print "Supported Services scan finished!"
	print "\n\n============================================================="
	devq.operate(Operate.STOP)
	return supported_services
#/// what definitions of subfunctions???  each service has its own subfunctions  
def discoversubfunctions(dev,supported_services=[],timeout=1):   #Scans for subfunctions of a given service.
	
	print("Starting discovering subfunctions of services")
	print supported_services

	if supported_services == None:
		return None
	#/// explain???  no meaning of datatemp here, just for init. byte0~byte7 will get data in the below
	datatemp = [0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
	fr = CAN_Packet()
	fr.configure(0x00,8,datatemp)

	vtmsgbuffer = []
	VTlogfile = VTlog()

	devq = ISOTP_driver(dev)
	devq.operate(Operate.START)
	count = 0
	supported_subfunc = []
	


	#/// make comments???
	for i in range(0,len(supported_services)): #travse all dsts and related supported services; byte2 & byte3 will represent the subfunctions
		fr.id = supported_services[i][0]
		#/// explain???
		for j in range(2,8): #from byte2 to byte7
			vtmsgbuffer = []
			datatemp[0]=j		
			datatemp[1]=supported_services[i][2]
			for l in range (0,256):						
				datatemp[3]=l
				for m in range (0,256):	
					datatemp[2]=m
					fr.data = datatemp
					devstatusflag = True
					while devstatusflag:
						devq.send_packet(fr)
						print fr		
						vtmsg = VTMessage(fr.id,8,fr.get_payload(),1,0.01,"S","Send Frame")
						vtmsgbuffer.append(vtmsg)

						recvfr,devstatusflag = devq.get_packet(timeout, filter=supported_services[i][1])
						
						
						if recvfr != None and recvfr.get_payload()[3] == 0x78:  #wait for correct response    0x78: 'requestCorrectlyReceivedResponsePending'
							print recvfr
							recvfr,devstatusflag = devq.get_packet(timeout, filter=supported_services[i][1])
							print recvfr
							vtmsg = VTMessage(recvfr.id,8,recvfr.get_payload(),1,0.01,"R","Recieve Frame")
							vtmsgbuffer.append(vtmsg)

						if devstatusflag:
							devstatusflag = False
						else:
							devstatusflag = True
				
									#time.sleep(0.01) 
						#/// explain???		recvfr.data[1]-0x40 == datatemp[1] means node comfirm it supoort this subfunction.  recvfr.data[1]==0x7f means node support the subfunction but have errors
						if recvfr != None and recvfr.get_payload()[3] != 0x13:  #0x13:incorrectMessageLengthOrInvalidFormat
							print recvfr
							vtmsg = VTMessage(recvfr.id,8,recvfr.get_payload(),1,0.01,"R","Recieve Frame")
							vtmsgbuffer.append(vtmsg)

							if recvfr.get_payload()[1]-0x40 == datatemp[1] or (recvfr.get_payload()[1]==0x7f and recvfr.data[3] not in [0x11,0x12,0x31,0x78]):
								count = count + 1
								supported_subfunc.append([supported_services[i],datatemp[2],datatemp[3]])
								service_name = SERVICE_NAMES.get(fr.get_payload()[1], "Unknown service")
								if recvfr.get_payload()[3] in [0x33,0x35,0x7E,0x7F]:	
									print "==================================="
									print("%d: 0x%X %s 0x%X 0x%X %s: 0x%X 0x%X" % (count,fr.id,"Supported subfunctions of Services in high security level",datatemp[0],datatemp[1],service_name, datatemp[2],datatemp[3]))
									print "==================================="	
									vtmsgbuffer[-1]= VTMessage(recvfr.id,8,recvfr.get_payload(),1,0.01,"K",service_name)						
						
								elif recvfr.get_payload()[0] > 0x07:  #Node response long length data
									print("%d: 0x%X %s 0x%X 0x%X %s: 0x%X 0x%X" % (count,fr.id,"get data stream",datatemp[0],datatemp[1],service_name,datatemp[2],datatemp[3]))
									print "==================================="
									time.sleep(0.5)
								else:
									print "==================================="
									print("%d: 0x%X %s 0x%X 0x%X %s: 0x%X 0x%X" % (count,fr.id,"Supported subfunctions of Services",datatemp[0],datatemp[1],service_name,datatemp[2],datatemp[3]))
									vtmsgbuffer[-1]= VTMessage(recvfr.id,8,recvfr.get_payload(),1,0.01,"K",service_name)
									print "==================================="
								
								
								
				
							#fill in the rest data bytes randomly
						if j > 2:		#fuzzing rest bytes of data
							for n in range(4,8):
								seed = random.randint(0,255)
								datatemp[n] = seed
								fr.data = datatemp
					

			logname = VTlogfile.writelog(vtmsgbuffer)
			print "\n\n============================================================="
			print("\nlog file: %s" % (logname))

	print "\n\n============================================================="
	print "Supported Subfunctions of Services scan finished!"
	devq.operate(Operate.STOP)
	return supported_subfunc


if __name__ == "__main__":
	#/// cangendata.py or uds-services-discovery.py???  It's worng, should be print "Usage: python uds_services_discovery.py <candev> "
	print "Usage: python uds_services_discovery.py <candev> <baudrate> <timeout>"

	dsts = []
	supported_services = []
	supported_subfunc = []
	
	
	dev = CANDriver(TypeCan.SERIAL,port=sys.argv[1],bit_rate=int(sys.argv[2]))
	dev.operate(Operate.START)

	dsts = discoverdst(dev,float(sys.argv[3]))	

	supported_services = discoverservices(dev,dsts,float(sys.argv[3]))

	#supported_services = [[1956, 1964, 16], [1956, 1964, 17], [1956, 1964, 20], [1956, 1964, 25], [1956, 1964, 34], [1956, 1964, 39], [1956, 1964, 40], [1956, 1964, 46], [1956, 1964, 47], [1956, 1964, 49], [1956, 1964, 62], [1956, 1964, 133], [2015, 1964, 16], [2015, 1964, 17], [2015, 1964, 20], [2015, 1964, 25], [2015, 1964, 34], [2015, 1964, 39], [2015, 1964, 40], [2015, 1964, 46], [2015, 1964, 47], [2015, 1964, 49], [2015, 1964, 62], [2015, 1964, 133]]

	supported_subfunc = discoversubfunctions(dev,supported_services,float(sys.argv[3]))
	print dsts,supported_services,supported_subfunc

	exit()





