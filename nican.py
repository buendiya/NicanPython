import os
import logging
from ctypes import *
import ctypes.wintypes as wintypes


# status
STATUS_OK = 0

NC_TRUE = 1

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

class VCI_CAN_OBJ(Structure):
    _fields_ = [
            ('ID', c_uint),
            ('TimeStamp', c_uint),
            ('TimeFlag', c_byte),
            ('SendType', c_byte),
            ('RemoteFlag', c_byte),
            ('ExternFlag', c_byte),
            ('DataLen', c_byte),
            ('Data', c_byte*8),
            ('Reserved', c_byte*3),
            ]


_cur_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] = os.path.pathsep.join([_cur_dir, os.environ['PATH']])
_dll_file = os.path.join(_cur_dir, 'nican.dll')
nican = windll.LoadLibrary(_dll_file)

def NC_StatusToString(Status, SizeofString, ErrorString):
    nican.ncStatusToString(Status, SizeofString, ErrorString)
    
def processStatus(status, source):
    if status == STATUS_OK:
        return
    elif status > 0:
        print "Warning: %s" % source
    else:
        ErrorString = (c_char*1024)()
        NC_StatusToString(status, len(ErrorString), ErrorString)
        print("\n%s\nSource = %s\n" % (ErrorString, source))
        raise Exception("\n%s\nSource = %s\n" % (ErrorString, source))
    
def NC_Config(objName, NumAttrs, AttrIdList, AttrValueList):
    status = nican.ncConfig(objName, NumAttrs, AttrIdList, AttrValueList)
    print("status: %s, type: %s" % (status, type(status)))
    processStatus(status, "NC_Config")
    
def NC_OpenObject(objName, objHandle):
    status = nican.ncOpenObject(objName, objHandle)
    processStatus(status, "NC_OpenObject")

def NC_ReadMult(objHandle, SizeofData, Data, ActualDataSize):
    status = nican.ncReadMult(objHandle, SizeofData, Data, ActualDataSize)
    processStatus(status, "NC_ReadMult")
    
def NC_Write(objHandle, SizeofData, Data):
    status = nican.ncWrite(objHandle, SizeofData, Data)
    processStatus(status, "NC_Write")

