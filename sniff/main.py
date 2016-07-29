import sys
import time
import os
import shutil
import logging
from multiprocessing import Process, Value, Array
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
frame_comment = []
task_data = None
task_key = None
name_devices = None

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
	for i in range(len(array_f)):
		log_file_1.debug(str(array_f[i]))

def write_log_2():
	for i in range(len(frame_comment)):
		log_file_2.debug(frame_comment[i].print_comment())

def print_frame(frame):
	result = "id: %d, dlc: %d," %(frame.id,frame.dlc)
	if(frame.category == 1):
		result = result + " Category: High Frequently, data = {"
	elif(frame.category == 2):
		result = result + " Category: Low Frequently, data = {"
	elif(frame.category == 3):
		result = result + " Category: Stable, data = {"
	for i in range(frame.dlc):
		if (i == frame.dlc-1):
			if i == frame.no_data:
				result = result + bcolors.RED + " %d"%(frame.data[i]) + bcolors.END + "}"
			else:
				result = result + " %d}" %frame.data[i]
		else:
			if i == frame.no_data:
				result = result + bcolors.RED + " %d"%(frame.data[i]) + bcolors.END + ","
			else:
				result = result + " %d," %frame.data[i]
	print result

def add_frame(frame):
	if(len(array_f) < 1):
		array_f.append(frame)
		print_frame(frame)
	else:
		count = 0
		for j in range(len(array_f)):
			if(array_f[j].compare(frame) == 0):
				count = count + 1
			if (count == len(array_f)):
				array_f.append(frame)
				print_frame(frame)
	return frame

#True:if added byte comment
def check_added_comment(frame,byte):
	s_byte = "byte%d"%byte
	d_comment = frame.get_comment()
	for b,c in d_comment.items():
		if(b == s_byte):
			return True
	return False

def add_comment_frame(comment,frame):
	for i in range(len(frame_comment)):
		if (frame.id == frame_comment[i].id):
			if(check_added_comment(frame_comment[i],frame.no_data)):
				frame_comment[i].add_comment(frame.no_data,comment)
			return
	frame.add_comment(frame.no_data,comment)
	frame_comment.append(frame)
	
def end_task():
	task_data.terminate()

def groud_data_task(flags,flags_comment,queue_frame_comment):
	#open devices
	dev = CantactDev(name_devices)
	dev.start()

	#set time
	time_pause = 0
	t_pause = 0
	start_time = time.time()

	#while in 2 min and not press 'q' to exit
	while((time.time()-start_time) < (2*60 + time_pause) and (flags.value != 2)):
		if(flags.value == 0):
			if(t_pause != 0):
				time_pause = time_pause + (time.time() - t_pause)
				t_pause = 0
			frame = dev.recv()
			add_frame(frame)
		elif(flags.value == 1):
			if t_pause == 0:
				t_pause = time.time()

	#write all data in log_1 file
	write_log_1()
	print 'End groud data frame'

	while(flags.value != 2):
		frame = dev.recv()
		frame_t = add_frame(frame)

		#if frame have category is LFCDF
		if(frame_t.category == 2):
			flags_comment.value = 1	
			queue_frame_comment.put(frame_t)
			print "\nplease comment the affection:"
			while(flags_comment.value != 0):
				time.sleep(0.1)
			
		
def start_task(flags,flags_comment,queue_frame_comment):
	task_data = Process(target=groud_data_task,args=(flags,flags_comment,queue_frame_comment,))
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
	#start process
	start_task(flags,flags_comment,queue_frame_comment)
	
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
				flags.value = 0
				print '========RUNNING========'

		elif(flags_comment.value == 1):
			frame = queue_frame_comment.get()
			add_comment_frame(c,frame)
			flags_comment.value = 0

	#write all data in log_2 file
	write_log_2()
			
			
	
	
	
