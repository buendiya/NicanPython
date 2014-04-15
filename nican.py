import os
from ctypes import *


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

# A T T R I B U T E   I D S
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

# Error
NICAN_ERROR_BASE = 0xBFF62000
CanErrNotStopped = NICAN_ERROR_BASE | 0X007

# NCTYPE_OPCODE values
NC_OP_START = 0x80000001
NC_OP_STOP = 0x80000002
NC_OP_RESET = 0x8000003

# NCTYPE State
NC_ST_READ_AVAIL = 0x00000001
NC_ST_WRITE_SUCCESS = 0x00000002
NC_ST_STOPPED = 0x00000004
NC_ST_READ_MULT = 0x00000008
NC_ST_ERROR = 0x00000010
NC_ST_WARNING = 0x00000020
NC_ST_REMOTE_WAKEUP = 0x00000040
NC_ST_WRITE_MULT = 0x0000080

#Frame type for CAN frames
NC_FRMTYPE_DATA = 0
NC_FRMTYPE_REMOTE = 0x01
NC_FRMTYPE_COMM_ERR = 0x02     #Communication warning/error (NC_ATTR_LOG_COMM_ERRS)
NC_FRMTYPE_RTSI = 0x03     #RTSI pulse (NC_ATTR_RTSI_MODE=NC_RTSI_TIME_ON_IN)
NC_FRMTYPE_TRIG_START = 0x04
NC_FRMTYPE_DELAY = 0x05    #Adds a delay between 2 timestamped frames.
NC_FRMTYPE_BUS_ERR = 0x06 
NC_FRMTYPE_TRANSCEIVER_ERR = 0x07

class NCTYPE_CAN_FRAME(Structure):
    _fields_ = [
            ('ArbitrationId', c_ulong),
            ('IsRemote', c_ubyte),
            ('DataLength', c_ubyte),
            ('Data', c_ubyte*8),
            ]

class NCTYPE_CAN_STRUCT(Structure):
    _pack_ = 1
    _fields_ = [
            ('Timestamp', c_ulonglong),
            ('ArbitrationId', c_ulong),
            ('FrameType', c_ubyte),
            ('DataLength', c_ubyte),
            ('Data', c_ubyte*8),
            ]

_cur_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] = os.path.pathsep.join([_cur_dir, os.environ['PATH']])
_dll_file = os.path.join(_cur_dir, 'Nican.dll')
print _dll_file
nican = windll.LoadLibrary(_dll_file)

    
def processStatus(status, source):
    if status == STATUS_OK:
        print "%s succeed" % source
    elif status > 0:
        print "Warning: %s" % source
    else:
        print "Error code: %x" % (c_uint32(status).value)
#         if c_uint32(status).value == CanErrNotStopped:
#             NC_Reset("CAN1", 0)
        ErrorString = (c_char*1024)()
        NC_StatusToString(status, sizeof(ErrorString), (ErrorString))
        raise Exception("\n%s\nSource = %s\n" % (ErrorString, source))

    
def NC_Action(objHandle, Opcode, Param):
    """Perform an action on an object.
    
    ncAction is a general purpose function you can use to perform an action on the object
    specified by ObjHandle. Its normal use is to start and stop network communication on a
    CAN Network Interface Object.
    
    Args:
        objHandle: c_ulong type. Object handle.
        Opcode: Operation code indicating which action to perform.
        Param: Parameter whose meaning is defined by Opcode.

    Returns:
        An int variable indicate Status returned from all NI-CAN functions.
        Status is zero for success, less than zero for an error, and greater than zero for a warning.
    """
    status = nican.ncAction(objHandle, Opcode, Param)
    processStatus(status, "NC_Action")

def NC_CloseObject(objHandle):
    """Close an object.

    ncCloseObject closes an object when it no longer needs to be in use, such as when the
    application is about to exit.
     
    Args:
        objHandle: c_ulong type. Object handle.

    Returns:
        Same with NC_Action.
    """    
    status = nican.ncCloseObject(objHandle)
    processStatus(status, "NC_CloseObject")
                                   
def NC_Config(objName, NumAttrs, AttrIdList, AttrValueList):
    """Configure an object before using it.
    
    ncConfig initializes the configuration attributes of an object before opening it.

    Args:
        objName: ASCII name of the object to configure.
        NumAttrs: Number of configuration attributes.
        AttrIdList: c_ulong array. List of configuration attribute identifiers.
        AttrValueList:  c_ulong array. List of configuration attribute values.

    Returns:
        Same with NC_Action.
    """    
    status = nican.ncConfig(objName, NumAttrs, AttrIdList, AttrValueList)
    processStatus(status, "NC_Config")
    
def NC_CreateNotification(objHandle, DesiredState, Timeout, RefData, Callback):
    """Create a notification callback for an object.

    Args:
        objHandle: c_ulong type. Object handle.
        DesiredState: States for which notification is sent.
        Timeout: Length of time to wait.
        RefData: Pointer to user-specified reference data.
        Callback: Address of your callback function.

    Returns:
        Same with NC_Action.
    """    
    status = nican.ncCreateNotification(objHandle, DesiredState, Timeout, RefData, Callback)
    processStatus(status, "NC_CreateNotification")

def NC_GetAttribute(objHandle, AttrId, SizeofAttr, Attr):
    """Get the value of an object attribute.

    Args:
        objHandle: c_ulong type. Object handle.
        AttrId: Identifier of the attribute to get.
        SizeofAttr: Parameter whose meaning is defined by Opcode.
        Attr: Output value. Size of the attribute in bytes.        

    Returns:
        Same with NC_Action.
    """    
    status = nican.ncGetAttribute(objHandle, AttrId, SizeofAttr, Attr)
    processStatus(status, "NC_GetAttribute")
                                    
def NC_OpenObject(objName, objHandle):
    """Open an object.

    Args:
        objName: ASCII name of the object to open.
        objHandle: c_ulong type. Output value. Object handle you use with all subsequent NI-CAN(ObjHandle out) function calls.

    Returns:
        Same with NC_Action.
    """    
    status = nican.ncOpenObject(objName, objHandle)
    processStatus(status, "NC_OpenObject")

def NC_Read(objHandle, SizeofData, Data):
    """Read the data value of an object.

    Args:
        objHandle: c_ulong type. Object handle.
        SizeofData: Size of the data in bytes.
        Data: Output value. Data read from object.

    Returns:
        Same with NC_Action.
    """    
    status = nican.ncRead(objHandle, SizeofData, Data)
    processStatus(status, "NC_Read")
    
def NC_ReadMult(objHandle, SizeofData, Data, ActualDataSize):
    """Read multiple data values from the queue of an object.

    Args:
        objHandle: c_ulong type. Object handle.
        SizeofData: Size of the data in bytes.
        Data: Output value. Data read from object.
        ActualDataSize: byref(c_ulong) type. Output value. The number of bytes actually returned. 

    Returns:
        Same with NC_Action.
    """    
    status = nican.ncReadMult(objHandle, SizeofData, Data, ActualDataSize)
    processStatus(status, "NC_ReadMult")
        
def NC_Reset(objName, Param):
    """Reset the CAN interface.

    Args:
        objName: ASCII name of the interface (card) to reset.
        Param: Reserved for future use.

    Returns:
        Same with NC_Action.
    """    
    status = nican.ncReset(objName, Param)
    processStatus(status, "NC_Reset")
    
def NC_SetAttribute(objHandle, AttrId, SizeofAttr, AttrPtr):
    """Set the value of an object's attribute.
    
    Args:
        objHandle: c_ulong type. Object handle.
        AttrId: Identifier of the attribute to set.
        SizeofAttr: Size of the attribute in bytes.
        AttrPtr: Output value. New attribute value. 

    Returns:
        Same with NC_Action.
    """    
    status = nican.ncSetAttribute(objHandle, AttrId, SizeofAttr, AttrPtr)
    processStatus(status, "NC_GetAttribute")

def NC_StatusToString(Status, SizeofString, ErrorString):
    """Convert status code into a descriptive string.

    Args:
        Status: Nonzero status code returned from NI-CAN function.
        SizeofString: Size of String buffer (in bytes).
        ErrorString: ASCII string that describes Status.

    Returns:
        Same with NC_Action.
    """    
    nican.ncStatusToString(Status, SizeofString, ErrorString) 

def NC_WaitForState(objHandle, DesiredState, Timeout, CurrentState):
    """Wait for one or more states to occur in an object.

    Args:
        objHandle: c_ulong type. Object handle.
        DesiredState: c_ulong type. States to wait for.
        Timeout: c_ulong type. Length of time to wait.
        CurrentState: Output value. Current state of object when desired states occur.

    Returns:
        Same with NC_Action.
    """    
    status = nican.ncWaitForState(objHandle, DesiredState, Timeout, CurrentState)
    processStatus(status, "NC_WaitForState") 
            
def NC_Write(objHandle, SizeofData, Data):
    """Write the data value of an object.

    Args:
        objHandle: c_ulong type. Object handle.
        SizeofData: Size of the data in bytes.
        Data: Data written to the object. 

    Returns:
        Same with NC_Action.
    """    
    status = nican.ncWrite(objHandle, SizeofData, Data)
    processStatus(status, "NC_Write")

def NC_WriteMult(objHandle, SizeofData, FrameArray):
    """Write the data value of an object.

    Args:
        objHandle: c_ulong type. Object handle.
        SizeofData: Size of the FrameArray in bytes.
        FrameArray: NCTYPE_CAN_FRAME array. FrameArray written to the object. 

    Returns:
        Same with NC_Action.
    """    
    status = nican.ncWriteMult(objHandle, SizeofData, FrameArray)
    processStatus(status, "NC_WriteMult")

# Ni-CAN attributes
default_num_attrs = 8
default_nican_config = {
                        NC_ATTR_BAUD_RATE: 250000, 
                        NC_ATTR_START_ON_OPEN: NC_TRUE, 
                        NC_ATTR_READ_Q_LEN: 150, 
                        NC_ATTR_WRITE_Q_LEN: 2, 
                        NC_ATTR_CAN_COMP_STD: 0, 
                        NC_ATTR_CAN_MASK_STD: NC_CAN_MASK_STD_DONTCARE, 
                        NC_ATTR_CAN_COMP_XTD: 0,
                        NC_ATTR_CAN_MASK_XTD: NC_CAN_MASK_XTD_DONTCARE,
                        }

default_interface = 'CAN1'
    
if __name__ == '__main__':
    try:      
#         interface = (c_char*7)()
#         interface.value = "CAN1"
        interface = default_interface
        AttrIdList = (c_ulong*8)(NC_ATTR_BAUD_RATE, 
                                    NC_ATTR_START_ON_OPEN, 
                                    NC_ATTR_READ_Q_LEN, 
                                    NC_ATTR_WRITE_Q_LEN, 
                                    NC_ATTR_CAN_COMP_STD, 
                                    NC_ATTR_CAN_MASK_STD, 
                                    NC_ATTR_CAN_COMP_XTD,
                                    NC_ATTR_CAN_MASK_XTD
                                    )
        AttrValueList = (c_ulong*8)(250000, NC_TRUE, 150, 2, 0, NC_CAN_MASK_STD_DONTCARE, 0, NC_CAN_MASK_XTD_DONTCARE)

        objHandle = c_ulong()
        # Configure the CAN Network Interface Object
        NC_Config(interface, 8, AttrIdList, AttrValueList)
        
        # Open the CAN Network Interface Object
        NC_OpenObject(interface, byref(objHandle))
        
        # Start communication
        NC_Action(objHandle, NC_OP_START, 0)
        
        NumFrames = 2
        Transmit = (NCTYPE_CAN_STRUCT*NumFrames)()
        for i in range(2):            
            Transmit[i].ArbitrationId = 1 | NC_FL_CAN_ARBID_XTD #pole_id
            Transmit[i].DataLength = 8
            Transmit[i].FrameType = NC_FRMTYPE_DATA
            Transmit[i].Timestamp = 0
            
            data = Transmit[i].Data
            data[0] = 1                 #pole_id
            data[1] = COMMAND_TYPE_WRITE
            data[2] = COMMAND_INDEX_LENGTH
            array = "%010X"%(i*10)          #length  
            for i in range(5):
                data[i+3] = int(array[i*2:i*2+2], 16)
        NC_WriteMult(objHandle, sizeof(Transmit), byref(Transmit))
          
#         data[0] = 1                 #pole_id
#         data[1] = COMMAND_TYPE_WRITE
#         data[2] = COMMAND_INDEX_LENGTH
#         array = "%010X"%0          #length  
#         for i in range(5):
#             data[i+3] = int(array[i*2:i*2+2], 16)
#         NC_Write(objHandle, sizeof(Transmit), byref(Transmit))
          
        # Wait for writing success
        state = c_ulong()
        timeout = c_ulong(100)
        NC_WaitForState(objHandle, NC_ST_WRITE_SUCCESS | NC_ST_WARNING | NC_ST_ERROR, timeout.value, byref(state))
        print "Writing state: 0x%08x" % state.value
        
        # Read
        ReceiveBuf = (NCTYPE_CAN_STRUCT*150)()
#         ReceiveBuf = NCTYPE_CAN_STRUCT()
        state = c_ulong()
        ActualDataSize = c_ulong()
        timeout = c_ulong(1000)
        print "Reading state: 0x%08x" % state.value

        NC_WaitForState(objHandle, NC_ST_READ_AVAIL | NC_ST_READ_MULT, timeout.value, byref(state))
        print "Reading state: 0x%08x" % state.value
        print state.value & (NC_ST_READ_AVAIL | NC_ST_READ_MULT)
        if state.value & (NC_ST_READ_AVAIL | NC_ST_READ_MULT):
            NC_ReadMult(objHandle, sizeof(ReceiveBuf), byref(ReceiveBuf), byref(ActualDataSize))
    #         NC_Read(objHandle, sizeof(ReceiveBuf), byref(ReceiveBuf))
            print "ActualDataSize = %d, sizeof(NCTYPE_CAN_STRUCT): %d" % (ActualDataSize.value, sizeof(NCTYPE_CAN_STRUCT))
            size = ActualDataSize.value / sizeof(NCTYPE_CAN_STRUCT)
            print "Frame size:%d" % size
            for i in range(size):
                print "id: %d" % ReceiveBuf[i].Data[0]
        NC_CloseObject(objHandle)
        
    except Exception, e:
        print e

