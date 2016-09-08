import sys
sys.path.append("..")
from CanLib.CAN_Packet import *
from CanLib.CAN_Driver import *
from CanLib.vtlog import *
import time
import os
import shutil
from multiprocessing import Process, Value, Array,Manager
import multiprocessing
try:
    import queue
except ImportError:
    import Queue as queue

# This program is to sniffer can data automatically and revease the key data frame that take actions
# sudo python sniffmodule.py /dev/ttyACM0 125000
# or 
# sudo python3.4 sniffmodule.py vcan0

keyfrbuffer = []   #store key frames
array_f = []  #store frames array
array_print = []  #store print frames array
queue = multiprocessing.Queue()

class bcolors:
	RED = '\033[91m'
	BLUE = '\033[94m'
	END = '\033[0m'

def print_frame(frame):
	result = "id:0x%X, dlc:%d," %(frame.id,frame.get_len())
	if(frame.category == 1):
		result = result + "type:HF, data = ["
	elif(frame.category == 2):
		result = result + "type:LF, data = ["
	elif(frame.category == 3):
		result = result + "type:SF, data = ["
	for i in range(frame.get_len()):
		if (i == frame.get_len()-1):
			if frame.bytechangeflag[i]:
				result = result + bcolors.RED + "0x%X"%(frame.get_payload()[i]) + bcolors.END + "]"
			else:
				result = result + "0x%X]" %frame.get_payload()[i]
		else:
			if frame.bytechangeflag[i]:
				result = result + bcolors.RED + "0x%X"%(frame.get_payload()[i]) + bcolors.END + ","
			else:
				result = result + "0x%X," %frame.get_payload()[i] 
	return result

def print_all_frame(frame,array_print=[]):
	array_print = add_frame_array_print(frame)
	os.system("clear")
	for i in range(len(array_print)):
		printresult = print_frame(array_print[i])
		print ("%d %s "% (i+1,printresult))
	return array_print

def add_frame_array_print(frame,array_print=[]):
	if(len(array_print) < 1):
		array_print.append(frame)
		return array_print
	for i in range(len(array_print)):
		if(array_print[i].id == frame.id):
			array_print[i] = frame
			return array_print
	array_print.append(frame)
	return array_print

		

def add_frame(frame,array_f = [],array_print = []):
	

	if(len(array_f) < 1):
		array_f.append(frame)
		array_print = print_all_frame(frame,array_print)
	else:
		count = 0
		lastframechangeflag = 1
		tempflag = [0,0,0,0,0,0,0,0]
		
		for j in range(len(array_f),0,-1):
					
			cmpflag = array_f[j-1].compare(frame)

			if(cmpflag==2 and lastframechangeflag==1):
				lastframechangeflag = 0	
				tempflag = frame.bytechangeflag
							
			if(cmpflag == 0 or cmpflag == 2):
				count = count + 1
			else:
				break	

		frame.bytechangeflag = tempflag
		if (count == len(array_f)):
			array_f.append(frame)

		if(cmpflag!=1):
			array_print = print_all_frame(frame,array_print)

	return array_f,array_print



def fraquire(dev,aquiretime=20,array_f = []):  # array_f to store array of frames

	
	array_print = [] #to store array of printing frames
	start_time = time.time()

	#while in 2 min and not press 'q' to exit
	while((time.time()-start_time) < 1*aquiretime):		
		
		frame = None
		while(frame == None):
			frame,flag = dev.receive_driver()		
		array_f,array_print = add_frame(frame,array_f,array_print)
	return array_f

def statics_framearray(array_f):
	
	found_ids = [] #found id array
	statics_info = [] #data structure [canid, totalcount, totalchangecount, bytechangecount[0~7]]  frame change rate = totalchangecount/totalcount, bytechangerate=bytechangecount[i]/totalcount
	statics_info2 = [] #data structure [canid, totalcount, framechangerate, bytechangerate[0~7]]  frame change rate = totalchangecount/totalcount, bytechangerate=bytechangecount[i]/totalcount

	for i in range(len(array_f)):
		if array_f[i].id not in found_ids:		
			found_ids.append(array_f[i].id)
			statics_info.append([array_f[i].id,array_f[i].count,array_f[i].sibdcount,array_f[i].bytechangecount])			
			framgechangerate = round(float(array_f[i].sibdcount)/array_f[i].count,3)			
			bytechangeratearray = []
			for j in range(8):
				bytechangerate = round(float(array_f[i].bytechangecount[j])/array_f[i].count,3)
				bytechangeratearray.append(bytechangerate)
			statics_info2.append([array_f[i].id,array_f[i].count,framgechangerate,bytechangeratearray])
				

	print (statics_info)
	print (statics_info2)

	return statics_info,statics_info2

def get_keyframearray(array_f_backgroud,array_f_new):  #to do more use  array_f_backgroud,array_f_new directly

	foundid_old = []
	statics_info0 = []
	statics_info_rate0 = []
	
	statics_info = []
	statics_info_rate = []

	keyfrarray = []	

	statics_info0,statics_info_rate0 = statics_framearray(array_f_backgroud)
	statics_info,statics_info_rate = statics_framearray(array_f_new)	

	for i in range(len(array_f_backgroud)):
		foundid_old.append(array_f_backgroud[i].id)

	for i in range(len(array_f_new)):
		if  array_f_new[i].id not in foundid_old:
			keyfrarray.append(array_f_new[i])
			
	
	#Mark key frames, make filter data as minus number
	
	for k in range(len(statics_info)):
		for i in range(len(array_f_new)):
			if statics_info[k][0] == array_f_new[i].id:
				for j in range(8):
					if array_f_new[i].bytechangecount[j] > 0:
						array_f_new[i].bytechangecount[j] = array_f_new[i].bytechangecount[j]*statics_info[k][3][j]

	#get key frames
	datatemp = [] #key byte id, to realize store different bytes

	for n in range(len(statics_info)):
		frcount = 0
		for i in range(len(array_f_new)-1,0,-1):
			if frcount > 8:
					datatemp = []
					break
			if statics_info[n][0] == array_f_new[i].id:				
				for j in range(8):
					if array_f_new[i].bytechangecount[j] > 0:
						frcount += 1
						
						if frcount ==1:
							keyfrarray.append(array_f_new[i])
							print (array_f_new[i].id,array_f_new[i].get_payload(),j,array_f_new[i].bytechangecount[j],array_f_new[i].bytechangecount)
							datatemp.append(array_f_new[i].get_payload()[j])
							break
						else:
							if array_f_new[i].get_payload()[j] not in datatemp :
								print (array_f_new[i].id,array_f_new[i].get_payload(),j,array_f_new[i].bytechangecount[j],array_f_new[i].bytechangecount)
								keyfrarray.append(array_f_new[i])		#get key frames
								datatemp.append(array_f_new[i].get_payload()[j])
							break
	
	return keyfrarray

def logfrarray2file(array_f,frtype = "P",frcomment = ""):

	#Record broudgroud frames of testing bus
	vtmsgbuffer = []
	VTlogfile = VTlog()

	for i in range(len(array_f)):
		vtmsg = VTMessage(array_f[i].id,8,array_f[i].get_payload(),array_f[i].count,0.01,frtype,frcomment)
		vtmsgbuffer.append(vtmsg)

	logname = VTlogfile.writelog(vtmsgbuffer)

	print("\nlog file: %s \n" % (logname))
	
	return logname

def replayarray1b1(frarray=[]):

	vtmsgbuffer = []
	VTlogfile = VTlog()

	#replay to confirm
	for i in range(len(frarray)):		
		fr = frarray[i]	
		flags_comment = 1
		while(flags_comment != 0):
			for k in range(10):
				dev.send_driver(fr)
			print (fr)
			if(sys.version_info >= (3,0)):
				c = input("Import frame? (write comment directly), press r to repeat and Enter directly to proceed\n")
			else:
				c = raw_input("Import frame? (write comment directly), press r to repeat and Enter directly to proceed\n")
				
			if c == "r":
				flags_comment = 1			
			elif len(c) > 3:
				vtmsg = VTMessage(fr.id,8,fr.get_payload(),8,0.01,"K",c)
				vtmsgbuffer.append(vtmsg)
				flags_comment = 0
			else:
				flags_comment = 0
			
	logname = VTlogfile.writelog(vtmsgbuffer)
	print("\nlog file: %s" % (logname))
	

	return logname


		
if __name__ == "__main__":
	#get deveice name
	if (len(sys.argv) < 2):
		print ('You must specify one can device')
		exit(1)
	if(sys.version_info >= (3,3)):
		dev = CANDriver(TypeCan.SOCKET,name_dev=sys.argv[1])
	else:
		dev = CANDriver(TypeCan.SERIAL,port=sys.argv[1],bit_rate=int(sys.argv[2]))
	dev.operate(Operate.START)

	backgroudfrarray = []
	newfrarray = []
	keyfrarray = []
	longname = []

	#collect backgroud frames of bus
	backgroudfrarray = fraquire(dev,20)

	VTlogfile = VTlog()
	longname.append(VTlogfile.logfrarray2file(VTlogfile,backgroudfrarray,"BR","Backgroud frames of testing bus"))
	print ('End group data frame')

	#filter unstable bytes
	for i in range(len(backgroudfrarray)):
		for j in range(8):
			if backgroudfrarray[i].bytechangecount[j] > 0:
				backgroudfrarray[i].bytechangecount[j] = -1
	
	if(dev.type == TypeCan.SOCKET):
		c = input("Please take action to change the vehicle status in 1 minutes(Press Enter to continue)...")
	elif(dev.type == TypeCan.SERIAL):
		c = raw_input("Please take action to change the vehicle status in 1 minutes(Press Enter to continue)...")

	VTlogfile = VTlog()
	newfrarray = fraquire(dev,30,backgroudfrarray)
	longname.append(VTlogfile.logfrarray2file(VTlogfile,newfrarray,"NR","New frames of testing bus"))
	
	VTlogfile = VTlog()
	keyfrarray = get_keyframearray(backgroudfrarray,newfrarray)
	longname.append(VTlogfile.logfrarray2file(VTlogfile,keyfrarray,"KR","Key frames of testing bus"))
	
	if(dev.type == TypeCan.SOCKET):
		c = input("Reversing done! Please press Enter to replay key frames(Press Enter to continue)...")
	elif(dev.type == TypeCan.SERIAL):
		c = raw_input("Reversing done! Please press Enter to replay key frames(Press Enter to continue)...")
	
	replayarray1b1(keyfrarray)

	for i in range(len(longname)):
		print (longname[i])

	exit()
	


	
	
