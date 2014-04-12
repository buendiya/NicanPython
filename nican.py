import os
import logging
from ctypes import *
import ctypes.wintypes as wintypes


# status
STATUS_OK = 0

NC_TRUE = 1

COMMAND_TYPE_WRITE = 0
COMMAND_TYPE_READ = 1
COMMAND_INDEX_STATUS = 1
COMMAND_INDEX_LENGTH = 2
COMMAND_INDEX_RESET = 4
COMMAND_INDEX_ID = 51 # 0x33
COMMAND_INDEX_MAX = 52 # 0x34

#A T T R I B U T E   I D S
NC_ATTR_BAUD_RATE = 0x80000007
NC_ATTR_START_ON_OPEN = 0x80000006
NC_ATTR_READ_Q_LEN = 0x80000013
NC_ATTR_WRITE_Q_LEN = 0x80000014
NC_ATTR_CAN_COMP_STD = 0x80010001
NC_ATTR_CAN_MASK_STD = 0x80010002
NC_CAN_MASK_STD_DONTCARE = 0x00000000
NC_ATTR_CAN_COMP_XTD = 0x80010003
NC_ATTR_CAN_MASK_XTD = 0x80010004
NC_CAN_MASK_XTD_DONTCARE = 0x00000000
NC_FL_CAN_ARBID_XTD = 0x20000000

#Error
NICAN_ERROR_BASE = 0xBFF62000
CanErrNotStopped = NICAN_ERROR_BASE | 0X007

class NCTYPE_CAN_FRAME(Structure):
    _fields_ = [
            ('ArbitrationId', c_ulong),
            ('IsRemote', c_ubyte),
            ('DataLength', c_ubyte),
            ('Data', c_ubyte*8),
            ]

_cur_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] = os.path.pathsep.join([_cur_dir, os.environ['PATH']])
_dll_file = os.path.join(_cur_dir, 'Nican.dll')
print _dll_file
nican = windll.LoadLibrary(_dll_file)

def NC_StatusToString(Status, SizeofString, ErrorString):
    nican.ncStatusToString(Status, SizeofString, ErrorString)
    
def processStatus(status, source):
    if status == STATUS_OK:
        print "%s succeed" % source
    elif status > 0:
        print "Warning: %s" % source
    else:
        print "Error: %x" % (c_uint32(status).value)
#         if c_uint32(status).value == CanErrNotStopped:
#             NC_Reset("CAN1", 0)
        ErrorString = (c_char*1024)()
        NC_StatusToString(status, len(ErrorString), ErrorString)
##        print("\n%s\nSource = %s\n" % (ErrorString, source))
        raise Exception("\n%s\nSource = %s\n" % (ErrorString, source))
    
def NC_Config(objName, NumAttrs, AttrIdList, AttrValueList):
    status = nican.ncConfig(objName, NumAttrs, AttrIdList, AttrValueList)
##    print("status: %s, type: %s" % (status, type(status)))
    processStatus(status, "NC_Config")
    
def NC_OpenObject(objName, objHandle):
    status = nican.ncOpenObject(objName, objHandle)
    processStatus(status, "NC_OpenObject")

def NC_CloseObject(objHandle):
    status = nican.ncCloseObject(objHandle)
    processStatus(status, "NC_CloseObject")

def NC_ReadMult(objHandle, SizeofData, Data, ActualDataSize):
    status = nican.ncReadMult(objHandle, SizeofData, Data, ActualDataSize)
    processStatus(status, "NC_ReadMult")
    
def NC_Write(objHandle, SizeofData, Data):
    status = nican.ncWrite(objHandle, SizeofData, Data)
    processStatus(status, "NC_Write")
    
def NC_Reset(objName, Param):
    status = nican.ncReset(objName, Param)
    processStatus(status, "NC_Reset")

    
if __name__ == '__main__':
    try:      
        interface = (c_char*7)()
        interface.value = "CAN1"
        AttrIdList = (c_ulong*8)(NC_ATTR_BAUD_RATE, 
                                    NC_ATTR_START_ON_OPEN, 
                                    NC_ATTR_READ_Q_LEN, 
                                    NC_ATTR_WRITE_Q_LEN, 
                                    NC_ATTR_CAN_COMP_STD, 
                                    NC_ATTR_CAN_MASK_STD, 
                                    NC_ATTR_CAN_COMP_XTD,
                                    NC_ATTR_CAN_MASK_XTD
                                    )
        AttrValueList = (c_ulong*8)(250000, NC_TRUE, 0, 1, 0, NC_CAN_MASK_STD_DONTCARE, 0, NC_CAN_MASK_XTD_DONTCARE)

        objHandle = c_ulong()
        #Configure the CAN Network Interface Object
        NC_Config(interface, 8, AttrIdList, AttrValueList)
        
        #open the CAN Network Interface Object
        NC_OpenObject(interface, byref(objHandle))
        
        Transmit = NCTYPE_CAN_FRAME()
        Transmit.ArbitrationId = 1 | NC_FL_CAN_ARBID_XTD #pole_id
        Transmit.IsRemote = 0
        Transmit.DataLength = 8
        data = Transmit.Data
        data[0] = 1                 #pole_id
        data[1] = COMMAND_TYPE_WRITE
        data[2] = COMMAND_INDEX_RESET
        array = "%010X"%0          #length  
        for i in range(5):
            data[i+3] = int(array[i*2:i*2+2], 16)
        NC_Write(objHandle, sizeof(Transmit), byref(Transmit))
        
        NC_CloseObject(objHandle)
        NC_Reset("CAN1", 0)

    except Exception, e:
        print e

