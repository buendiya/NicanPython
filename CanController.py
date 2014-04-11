import time
import logging
from nican import *

logger = logging.getLogger('shiyijian.robot')

status = {}

default_devicetype = 4
default_deviceind = 0
default_canind = 0
default_can_config = {
        'AccCode': 0x0,
        'AccMask': 0xFFFFFFFF,
        'Filter': 1,
        'Timing0': 0x01,
        'Timing1': 0x1C,
        'Mode': 0,
        }
default_receive_timeout = 5

COMMAND_TYPE_WRITE = 0
COMMAND_TYPE_READ = 1
COMMAND_INDEX_STATUS = 1
COMMAND_INDEX_LENGTH = 2
COMMAND_INDEX_RESET = 4
COMMAND_INDEX_ID = 51 # 0x33
COMMAND_INDEX_MAX = 52 # 0x34
COMMAND_INDEX_DICT = {
                      'LENGTH': COMMAND_INDEX_LENGTH,
                      'ID': COMMAND_INDEX_ID,
                      'MAX': COMMAND_INDEX_MAX,
                      }    
RESPONSE_OK = 1
RESPONSE_ERROR = 0


class CanError(StandardError):
    def __init__(self, desc, obj):
        self.desc = desc
    
    def __str__(self):
        return self.desc

def _byte_to_hex_string(num):
    if num < 0:
        num = num + 256
    return "%02X"%num

class CommandFrame(object):
    def __init__(self, pole_id):
        self.id = pole_id
        self.command_buffer = None
        self.command_type = None
        self.command_index = None
        self.command_data = None

    def fillStructure(self, vco):
        vco.ID = self.id
        vco.SendType = 0
        vco.RemoteFlag = 0
        vco.ExternFlag = 1
        vco.DataLen = 8
        data = vco.Data
        data[0] = self.id
        data[1] = self.command_type
        data[2] = self.command_index
        array = "%010X"%self.command_data
        for i in range(5):
            data[i+3] = int(array[i*2:i*2+2], 16)
        self.command_buffer = vco

    def __repr__(self):
        if self.command_buffer is None:
            return 'EMPTY'
        return "".join(_byte_to_hex_string(self.command_buffer.Data[i]) for i in range(8))


class SetLengthCommandFrame(CommandFrame):
    def __init__(self, pole_id, length):
        super(SetLengthCommandFrame, self).__init__(pole_id)
        self.command_index = COMMAND_INDEX_LENGTH
        self.command_type = COMMAND_TYPE_WRITE
        self.command_data = length
        

class ChangeIDCommandFrame(CommandFrame):
    def __init__(self, pole_id, new_pole_id):
        super(ChangeIDCommandFrame, self).__init__(pole_id)
        self.command_index = COMMAND_INDEX_ID
        self.command_type = COMMAND_TYPE_WRITE
        self.command_data = new_pole_id
        
class ResetCommandFrame(CommandFrame):
    def __init__(self, pole_id):
        super(ResetCommandFrame, self).__init__(pole_id)
        self.command_index = COMMAND_INDEX_RESET
        self.command_type = COMMAND_TYPE_WRITE
        self.command_data = 0
        
class SetMaxLengthCommandFrame(CommandFrame):
    def __init__(self, pole_id, max_length):
        super(SetMaxLengthCommandFrame, self).__init__(pole_id)
        self.command_index = COMMAND_INDEX_MAX
        self.command_type = COMMAND_TYPE_WRITE
        self.command_data = max_length
        
class ReadStatusCommandFrame(CommandFrame):
    def __init__(self, pole_id, status):
        super(ReadStatusCommandFrame, self).__init__(pole_id)
        self.command_index = COMMAND_INDEX_DICT[status]
        self.command_type = COMMAND_TYPE_READ
        self.command_data = 0


class ResponseFrame(object):
    def __init__(self, obj):
        self.response_buffer = obj
        self.frame_id = obj.ID
        self.id = obj.Data[0]
        self.status = (obj.Data[1] == RESPONSE_OK)
        self.command = obj.Data[2]

    @property
    def data(self):
        return int("".join(_byte_to_hex_string(self.response_buffer.Data[i]) for i in range(3, 8)), 16)

    def __repr__(self):
        return "".join(_byte_to_hex_string(self.response_buffer.Data[i]) for i in range(8))


class ResponseSet(dict):
    def __init__(self, objs): # objs is a list
        super(ResponseSet, self).__init__()
        for obj in objs:
            response = ResponseFrame(obj)
            self[response.id] = response

class BodyModelData(dict):
    def __init__(self, *args, **kwargs):
        super(BodyModelData, self).__init__(*args, **kwargs)
        if 'index' in self:
            self.index = self.pop('index')
        else:
            self.index = '0'

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("Can't get attr %s from body model data" % name)

    def delta(self, data):
        delta = BodyModelDeltaData()
        for key in self:
            if self[key] != data[key]:
                delta[key] = self[key]
        return delta

    @staticmethod
    def parseFile(filename):
        f = open(filename, 'r')
        r = BodyModelData.parseFileLikeObject(f)
        f.close()
        r.index = unicode(os.path.splitext(os.path.basename(filename))[0])
        return r

    @staticmethod
    def parseFileLikeObject(obj):
        return BodyModelData.parseString(obj.read())

    @staticmethod
    def parseString(s):
        model = BodyModelData()
        datas = [line.strip() for line in s.split(',')]
        for i in range(len(datas)):
            model[i + 1] = int(float(datas[i]))
        return model

    @staticmethod
    def parseModelsFromFile(filename):
        f = open(filename, 'r')
        r = BodyModelData.parseModelsFromFileLikeObject(f)
        f.close()
        return r

    @staticmethod
    def parseModelsFromFileLikeObject(obj):
        return BodyModelData.parseModelsFromString(obj.read())

    @staticmethod
    def parseModelsFromString(s):
        s = ''.join([line.strip() for line in s.splitlines() if line.strip() and not line.strip().startswith("#")])
        models = BodyModels()
        model_lines = [line.strip() for line in s.split(";") if line]
        for line in model_lines:
            index, datas = line.split(":")
            model = BodyModelData.parseString(datas)
            model.index = unicode(index.strip())
            models[model.index] = model
        return models
    
    @staticmethod
    def serializeModels(models, ordered=True):
        sl = []
        if ordered:
            l = models.ordered
        else:
            l = sorted(models.keys(), cmp=_cmp)
        sl.append("#   %s\n"%",".join(["%03s"%i for i in range(len(models[l[0]]))]))
        for index in l:
            model = models[index]
            sl.append("%s:\n    "%index)
            sl.append(",".join(["%03s"%model[i] for i in sorted(model.keys())]))
            sl.append(";\n")
        return "".join(sl)
    
    @staticmethod
    def saveModelsToFile(models, filename, ordered=True):
        f = open(filename, 'w')
        f.write(BodyModelData.serializeModels(models, ordered))
        f.close()


def _cmp(x, y):
    try:
        return cmp(int(x), int(y))
    except ValueError:
        return cmp(x, y)


class BodyModelDeltaData(BodyModelData):
    pass


class BodyModels(dict):
    def __init__(self):
        super(BodyModels, self).__init__()
        self.ordered = []
        
    def autoSort(self):
        self.ordered.sort(cmp=_cmp)
    
    def __setitem__(self, i, y):
        if i not in self:
            self.ordered.append(i)
        super(BodyModels, self).__setitem__(i, y)
        
    def __delitem(self, i):
        super(BodyModels, self).__delitem__(i)
        self.ordered.remove(i)
        
    def update(self, *args, **kwargs):
        raise StandardError("update not support!")
    
    def pop(self, i, y=None):
        if i in self:
            self.ordered.remove(i)
        if y is None:
            super(BodyModels, self).pop(i)
        else:
            super(BodyModels, self).pop(i, y)

class RobotController(object):
    proxy = None
    def __init__(self):
        self.interface = (c_char*7)()
        self.interface.value = "CAN0"
        self.AttrIdList = (c_ulong*8)(NC_ATTR_BAUD_RATE, 
                                    NC_ATTR_START_ON_OPEN, 
                                    NC_ATTR_READ_Q_LEN, 
                                    NC_ATTR_WRITE_Q_LEN, 
                                    NC_ATTR_CAN_COMP_STD, 
                                    NC_ATTR_CAN_MASK_STD, 
                                    NC_ATTR_CAN_COMP_XTD,
                                    NC_ATTR_CAN_MASK_XTD
                                    )
        self.AttrValueList = (c_ulong*8)(125000, NC_TRUE, 0, 1, 0, NC_CAN_MASK_STD_DONTCARE, 0, NC_CAN_MASK_XTD_DONTCARE)

        self.objHandle = c_ulong()
        #Configure the CAN Network Interface Object
        NC_Config(self.interface, 8, self.AttrIdList, self.AttrValueList)
        
        #open the CAN Network Interface Object
        NC_OpenObject(self.interface, byref(self.objHandle))
        
    def transmit(self, command_frame):
        num = NC_Write(self.devicetype, self.deviceind, self.canind, command_frame)
        logger.debug(str(command_frame))
        if not num:
            logger.error('Failed to transmit command %s to pole %s' % (command_frame.command_index, command_frame.id))
            raise CanError('Failed to transmit data to can %s!' % self.canind, self)
        return num
    
    def readStatus(self, pole_id, status):
        return self.transmit(ReadStatusCommandFrame(pole_id, status))

    def setPoleLength(self, pole_id, length):  # length unit is mm
        # TODO: range is specified for each pole
        # if length < 50 or length > 600:
        #   raise AttributeError('length should be in range 50 ~ 600! %s %s'%(id, length))
        #if length < 50:
            #logger.warning('length should be larger than 50! %s %s' % (id, length))
            #length = 50
        #if length > 600:
            #logger.warning('length should be smaller than 50! %s %s' % (id, length))
            #length = 600
        if self.proxy is not None:
            pole_id = self.proxy[0][pole_id-1]
        return self.transmit(SetLengthCommandFrame(pole_id, length))
        
    def changePoleId(self, pole_id, new_pole_id):
        return self.transmit(ChangeIDCommandFrame(pole_id, new_pole_id))
    
    def resetPole(self, pole_id):
        return self.transmit(ResetCommandFrame(pole_id))
    
    def setPoleMaxLength(self, pole_id, max_length):
        return self.transmit(SetMaxLengthCommandFrame(pole_id, max_length))

#     def transferToModel(self, model, block=False, timeout=5, force=False, ignore_previous=False, interval=0):
#         if ignore_previous:
#             self.current_model = model
#             self.delta_model = model
#         else:
#             if self.current_model is None:
#                 self.current_model = model
#                 self.delta_model = model
#                 logger.info('transfer to model %s' % model.index)
#             else:
#                 self.delta_model = model.delta(self.current_model)
#                 logger.info('transfer from %s to model %s' % (self.current_model.index, model.index))
#         self.target_model = model
#         self.transferModelDeltaData(self.delta_model, block=block, timeout=timeout, force=force, interval=interval)
# 
#     def transferModelDeltaData(self, delta, block=False, timeout=5, force=False, interval=0):
#         for key in delta:
#             self.setPoleLength(key, delta[key])
#             if interval:
#                 time.sleep(interval)
#         if block:
#             self.waitForModelTransfer(timeout, force=force)
# 
#     def waitForModelTransfer(self, timeout=5, force=False):
#         logger.info('waiting for transfer to model %s' % self.target_model.index)
#         self.responses = self.receive(len(self.delta_model), timeout=timeout, force=force)
#         logger.info('transfered to model %s' % self.target_model.index)
#         self.delta_model = None
#         self.current_model = self.target_model
#         self.target_model = None

#     def receive(self, length=100, timeout=0, force=False):
#         self.received_frames = None
#         num = self.getReceiveNumber()
#         t = time.time()
#         if not timeout:
#             if num:
#                 self.received_frames = ResponseSet(VCI_Receive(self.devicetype, self.deviceind, self.canind, num, waittime=self.receive_timeout))
#             else:
#                 self.received_frames = ResponseSet([])
#             logger.debug('received: %s', self.received_frames)
#             return self.received_frames
#         while num < length and time.time() - t < timeout:
#             time.sleep(0.2)
#             num = self.getReceiveNumber()
#         if num < length and force:
#             self.received_frames = ResponseSet(VCI_Receive(self.devicetype, self.deviceind, self.canind, num, waittime=self.receive_timeout))
#             logger.debug(self.received_frames)
#             for id in self.received_frames:
#                 self.delta_model.pop(id)
#             logger.error("unable to receive %s poles' response" % self.delta_model.keys())
#             raise CanError('Failed to get receive %s frames in %ss' % (length, timeout), self)
#         else:
#             if num:
#                 self.received_frames = ResponseSet(VCI_Receive(self.devicetype, self.deviceind, self.canind, num, waittime=self.receive_timeout))
#             else:
#                 self.received_frames = ResponseSet([])
#             if self.proxy is not None:
#                 self.o_received_frames = self.received_frames
#                 self.received_frames = ResponseSet([])
#                 for k  in self.o_received_frames.keys():
#                     o_id = self.proxy[1][k-1]
#                     self.received_frames[o_id] = self.o_received_frames[k]
#             logger.debug('received: %s', self.received_frames)
#             return self.received_frames





_preceives = (VCI_CAN_OBJ*100)()
_psends = VCI_CAN_OBJ()


if __name__ == '__main__':
    try:      
        robot = RobotController()
        robot.setPoleLength(1, 1)

    except Exception, e:
        print e
        
