import sys
import time
import os
import shutil
import logging
from multiprocessing import Process, Value, Array,Manager
import multiprocessing
try:
    import queue
except ImportError:
    import Queue as queue

import can
from cantact import *

log_file_1 = None
log_file_2 = None
array_f = []
array_print = []
task_data = None
task_key = None
name_devices = None
queue = multiprocessing.Queue()
frame_comment = []

class bcolors:
	RED = '\033[91m'
	END = '\033[0m'

def setup_logger(logger_name, log_file, level=logging.DEBUG):
	l = logging.getLogger(logger_name)
	formatter = logging.Formatter('',datefmt='%m/%d/%Y-%I:%M:%S-%p')
	fileHandler = logging.FileHandler(log_file, mode='w')
	fileHandler.setFormatter(formatter)

	l.setLevel(level)
	l.addHandler(fileHandler)

def write_log_1():
	log_file_1.debug("[")
	for i in range(len(array_f)):
		if(i == (len(array_f)-1)):
			log_file_1.debug(array_f[i].print_log())
		else:
			log_file_1.debug(array_f[i].print_log())
			log_file_1.debug(",")
	log_file_1.debug("]")

def write_log_2():
	for i in range(len(frame_comment)):
		log_file_2.debug(frame_comment[i].print_comment())

def print_frame(frame):
	result = "id: 0x%X, dlc: %d," %(frame.id,frame.dlc)
	if(frame.category == 1):
		result = result + " Category: High Frequently, data = {"
	elif(frame.category == 2):
		result = result + " Category: Low Frequently, data = {"
	elif(frame.category == 3):
		result = result + " Category: Stable, data = {"
	for i in range(frame.dlc):
		if (i == frame.dlc-1):
			if i == frame.no_data:
				result = result + bcolors.RED + " 0x%X"%(frame.data[i]) + bcolors.END + "}"
			else:
				result = result + " 0x%X}" %frame.data[i]
		else:
			if i == frame.no_data:
				result = result + bcolors.RED + " 0x%X"%(frame.data[i]) + bcolors.END + ","
			else:
				result = result + " 0x%X," %frame.data[i]
	print result

def print_all_frame(frame):
	add_frame_array_print(frame)
	os.system("clear")
	for i in range(len(array_print)):
		print_frame(array_print[i])

def add_frame_array_print(frame):
	if(len(array_print) < 1):
		array_print.append(frame)
		return
	
	for i in range(len(array_print)):
		if(array_print[i].id == frame.id):
			array_print[i] = frame
			return
	array_print.append(frame)

#case frame exit in array, so update no_data for this frame
def update_no_data(frame):
	for j in range(len(array_f)):
			if(array_f[j].compare(frame) == 1):
				array_f[j].no_data = frame.no_data
				array_f[j].category = frame.category
		
#flags_show_all: True: display all; False: display frame
#step: 1: step 1, 2: step 2
def add_frame(frame,flags_show_all,step):
	if(len(array_f) < 1):
		array_f.append(frame)
		if(flags_show_all == True):
			print_all_frame(frame)
	else:
		count = 0
		for j in range(len(array_f)):
			if(array_f[j].compare(frame) == 0):
				count = count + 1
		if (count == len(array_f)):
			array_f.append(frame)
			if(flags_show_all == True):
				print_all_frame(frame)
		else:
			update_no_data(frame)
			
	return frame


#True:if added byte comment
def check_added_comment(frame,byte):
	s_byte = "byte%d"%byte
	d_comment = frame.get_comment()
	for b,c in d_comment.items():
		if(b == s_byte):
			return True
	return False

def update_queue_temp(frame_comment_t):
	for i in range(frame_comment_t.qsize()):
		frame_comment_t.get()
	for i in range(len(frame_comment)):
		frame_comment_t.put(frame_comment[i])

#True: can add comment
def check_added_comment_all(frame_comment_t,frame):
	a = []
	for i in range(frame_comment_t.qsize()):
		f = frame_comment_t.get()
		a.append(f)
		if (frame.id == f.id):
			if(check_added_comment(f,frame.no_data) == True):
				for k in range(len(a)):
					frame_comment_t.put(a[k])
				return False

	for k in range(len(a)):
		frame_comment_t.put(a[k])
	return True



def add_comment_frame(comment,frame):
	for i in range(len(frame_comment)):
		if (frame.id == frame_comment[i].id):
			frame_comment[i].add_comment(frame.no_data,comment)
			return

	frame.add_comment(frame.no_data,comment)
	frame_comment.append(frame)
			
def put_data_testing():
	#init data testing
	f = can.Frame(0x1,5,[0,1,2,3,0x10])
	queue.put(f)
	f = can.Frame(0x2,5,[0,1,2,3,0x12])
	queue.put(f)
	f = can.Frame(0x3,5,[0,1,2,3,0x24])
	queue.put(f)
	f = can.Frame(0x4,5,[0,1,2,3,0x23])
	queue.put(f)
	f = can.Frame(0x5,5,[0,1,2,3,0x4])
	queue.put(f)
	f = can.Frame(0x3,5,[0,1,2,3,0x54])
	queue.put(f)
	f = can.Frame(0x2,5,[0,1,2,3,0x34])
	queue.put(f)
	f = can.Frame(0x1,5,[0,1,2,3,0x12])
	queue.put(f)
	f = can.Frame(0x5,5,[0,1,2,3,0x11])
	queue.put(f)
	f = can.Frame(0x4,5,[0,1,2,3,0x12])
	queue.put(f)
	f = can.Frame(0x2,5,[0,1,2,3,0x23])
	queue.put(f)
	f = can.Frame(0x1,5,[0,1,2,3,0x33])
	queue.put(f)
	f = can.Frame(0x5,5,[0,1,2,3,0x3])
	queue.put(f)
	f = can.Frame(0x3,5,[0,0x3,2,3,0x15])
	queue.put(f)
	f = can.Frame(0x4,5,[0,1,0x6,3,0x16])
	queue.put(f)
	f = can.Frame(0x1,5,[0,1,2,3,0x54])
	queue.put(f)
	f = can.Frame(0x1,5,[0,0x3,2,3,0x54])
	queue.put(f)
	f = can.Frame(0x5,5,[0x0,1,2,3,0x3])
	queue.put(f)
	
def end_task():
	task_data.terminate()

def groud_data_task(flags,flags_comment,queue_frame_comment,frame_comment_t,queue):
	#open devices
	dev = CantactDev(name_devices)
	dev.stop()	
	dev.ser.write('S4\r')
	dev.start()

	#set time
	time_pause = 0
	t_pause = 0
	start_time = time.time()

	#while in 2 min and not press 'q' to exit
	while((time.time()-start_time) < (2*60 + time_pause) and (flags.value != 2)):
		#time.sleep(1)
		if(flags.value == 0):
			if(t_pause != 0):
				time_pause = time_pause + (time.time() - t_pause)
				t_pause = 0
			frame = dev.recv()
			add_frame(frame,True,1)
			#if(queue.empty() == False):
			#	frame = queue.get()
			#	add_frame(frame,True,1)
		elif(flags.value == 1):
			if t_pause == 0:
				t_pause = time.time()

	#write all data in log_1 file
	write_log_1()
	print 'End groud data frame'
	
	#put_data_testing()

	while(flags.value != 2):
		frame = dev.recv()
		frame_t = add_frame(frame,False,2)
		#time.sleep(1)
		#if(queue.empty() == False):
		#	frame = queue.get()
		#	frame_t = add_frame(frame,False,2)
			
		#if frame have category is LFCDF
		if(frame_t.category == 2 or frame_t.category == 1):
			if(check_added_comment_all(frame_comment_t,frame_t) == True):
				print_frame(frame_t)
				queue_frame_comment.put(frame_t)
				flags_comment.value = 1	
				print "\nplease comment the affection:"
				while(flags_comment.value != 0):
					time.sleep(0.1)
			
	
def start_task(flags,flags_comment,queue_frame_comment,frame_comment_t,queue):
	task_data = Process(target=groud_data_task,args=(flags,flags_comment,queue_frame_comment,frame_comment_t,queue,))
	task_data.start()

		
if __name__ == "__main__":
	#get deveice name
	if (len(sys.argv) < 2):
		print 'You must specify one can device'
		exit(1)
	else:
		name_devices = sys.argv[1]

	#setup log file
	setup_logger('log1', r'log1.log')
	setup_logger('log2', r'log2.log')
	log_file_1 = logging.getLogger('log1')
	log_file_2 = logging.getLogger('log2')

	#value flags:0 - Running, 1-pause, 2-exit
	flags = Value('d', 0.0)
	
	#value flags:0-no add comment; 1-add comment data
	flags_comment = Value('d', 0.0)
	
	queue_frame_comment = multiprocessing.Queue()
	frame_comment_t = multiprocessing.Queue()

	#init data testing
	#put_data_testing()

	#start process
	start_task(flags,flags_comment,queue_frame_comment,frame_comment_t,queue)
	
	#check key
	while(flags.value != 2):
		c = raw_input()
		if(flags_comment.value == 0):
			if(c == ' '):
				flags.value = 1
				print '========PAUSE========'
			elif(c == 'q'):
				flags.value = 2
				print '========EXIT========'
			else:
				if (flags.value == 1):
					flags.value = 0
					print '========RUNNING========'

		elif(flags_comment.value == 1):
			frame = queue_frame_comment.get()
			add_comment_frame(c,frame)
			update_queue_temp(frame_comment_t)
			flags_comment.value = 0

	#write all data in log_2 file
	write_log_2()
			
			
	
	
	
