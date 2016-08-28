import sys
class Const(object):
	def SET_BIT(self, val, bitIndex):
		val_0 = 1 << bitIndex
		val = val | val_0
		return val
	def CLEAR_BIT(self,val, bitIndex):
		val_0 = ~(1 << bitIndex)
		val = val & val_0
		return val
	def TOGGLE_BIT(self,val, bitIndex):
		val_0 = 1 << bitIndex
		val = val ^ val_0
		return val
	def IS_SET(self, val, bitIndex):
		val_0 = 1 << bitIndex
		val = val & val_0
		return val
	
	# OBD-II Modes
	OBD_MODE_SHOW_CURRENT_DATA 	= 0x01
	OBD_MODE_SHOW_FREEZE_FRAME 	= 0x02
	OBD_MODE_READ_DTC		= 0x03
	OBD_MODE_CLEAR_DTC              = 0x04
	OBD_MODE_TEST_RESULTS_NON_CAN   = 0x05
	OBD_MODE_TEST_RESULTS_CAN       = 0x06
	OBD_MODE_READ_PENDING_DTC       = 0x07
	OBD_MODE_CONTROL_OPERATIONS     = 0x08
	OBD_MODE_VEHICLE_INFORMATION    = 0x09
	OBD_MODE_READ_PERM_DTC          = 0x0A
	
	# UDS SIDs
	UDS_SID_DIAGNOSTIC_CONTROL        = 0x10 
	UDS_SID_ECU_RESET                 = 0x11
	UDS_SID_GM_READ_FAILURE_RECORD    = 0x12 
	UDS_SID_CLEAR_DTC                 = 0x14
	UDS_SID_READ_DTC                  = 0x19
	UDS_SID_GM_READ_DID_BY_ID         = 0x1A 
	UDS_SID_RESTART_COMMUNICATIONS    = 0x20 
	UDS_SID_READ_DATA_BY_ID           = 0x22
	UDS_SID_READ_MEM_BY_ADDRESS       = 0x23
	UDS_SID_READ_SCALING_BY_ID        = 0x24
	UDS_SID_SECURITY_ACCESS           = 0x27
	UDS_SID_COMMUNICATION_CONTROL     = 0x28
	UDS_SID_READ_DATA_BY_ID_PERIODIC  = 0x2A
	UDS_SID_DEFINE_DATA_ID            = 0x2C
	UDS_SID_WRITE_DATA_BY_ID          = 0x2E
	UDS_SID_IO_CONTROL_BY_ID          = 0x2F
	UDS_SID_ROUTINE_CONTROL           = 0x31
	UDS_SID_REQUEST_DOWNLOAD          = 0x34
	UDS_SID_REQUEST_UPLOAD            = 0x35
	UDS_SID_TRANSFER_DATA             = 0x36
	UDS_SID_REQUEST_XFER_EXIT         = 0x37
	UDS_SID_REQUEST_XFER_FILE         = 0x38
	UDS_SID_WRITE_MEM_BY_ADDRESS      = 0x3D
	UDS_SID_TESTER_PRESENT            = 0x3E
	UDS_SID_ACCESS_TIMING             = 0x83
	UDS_SID_SECURED_DATA_TRANS        = 0x84
	UDS_SID_CONTROL_DTC_SETTINGS      = 0x85
	UDS_SID_RESPONSE_ON_EVENT         = 0x86
	UDS_SID_LINK_CONTROL              = 0x87
	UDS_SID_GM_PROGRAMMED_STATE       = 0xA2
	UDS_SID_GM_PROGRAMMING_MODE       = 0xA5
	UDS_SID_GM_READ_DIAG_INFO         = 0xA9
	UDS_SID_GM_READ_DATA_BY_ID        = 0xAA
	UDS_SID_GM_DEVICE_CONTROL         = 0xAE

	# GM READ DIAG SUB FUNCS
	UDS_READ_STATUS_BY_MASK           = 0x81
	
	# DTC MASK Bitflags */
	DTC_SUPPORTED_BY_CALIBRATION      = 1
	DTC_CURRENT_DTC                   = 2
	DTC_TEST_NOT_PASSED_SINCE_CLEARED = 4
	DTC_TEST_FAILED_SINCE_CLEARED     = 8
	DTC_HISTORY                       = 16
	DTC_TEST_NOT_PASSED_SINCE_POWER   = 32
	DTC_CURRENT_DTC_SINCE_POWER       = 64
	DTC_WARNING_INDICATOR_STATE       = 128

	# Periodic Data Message types */
	PENDING_READ_DATA_BY_ID_GM        = 1
	
	CAN_RTR_FLAG 			  = 0x40000000
	
