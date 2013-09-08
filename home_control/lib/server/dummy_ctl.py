"""Base class for controller"""

import logging
import sys
import base_ctl
from pb import control_pb2

# Configure logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

global_values = { control_pb2.FEAT_PWR: control_pb2.POWER_OFF,
                  control_pb2.FEAT_INPUT: control_pb2.INPUT_RGB,
                  control_pb2.FEAT_PERCENT: 50}

class DummyCtl(base_ctl.BaseCtl):
    def __init__(self, device):
        """Initialize a controller for the time of the message.

        Arguments:
        device: type control_pb2.Device
        """
        
    def Get(self, msg):
        """Get the power status of a device.

        Arguments:
        msg: type control_pb2.GetRequest

	Returns:
        control_pb2.GetResponse
        """
        response = control_pb2.GetResponse()
        response.result = True
        response.value = global_values[msg.type]
        log.debug('Got %d: %d' % (msg.type, response.value))
	return response

    def Set(self, msg):
        """Set the power status of a device.

        Arguments:
        msg: type control_pb2.SetRequest

	Returns:
        control_pb2.SetResponse
        """
        global global_value
        log.debug('Got %d: %d' % (msg.type, msg.value))
        global_values[msg.type] = msg.value
        response = control_pb2.GetResponse()
        response.result = True
	return response


