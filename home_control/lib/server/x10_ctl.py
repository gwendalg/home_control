"""Class for X10 controller"""

import logging
import subprocess
import sys
import base_ctl
from pb import control_pb2

# Configure logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

PWR_COMMANDS = { control_pb2.POWER_ON: 'on',
                 control_pb2.POWER_OFF: 'off' }

class X10Ctl(base_ctl.BaseCtl):
    def __init__(self, device):
        """Initialize a controller for the time of the message.

        Arguments:
        device: type control_pb2.Device
        """
        self.cmd = ['/var/lib/x10/bin', 'turn', device.port]
        
    def Get(self, msg):
        """Get the power status of a device.

        Arguments:
        msg: type control_pb2.GetRequest

	Returns:
        control_pb2.GetResponse
        """
        if msg.type != control_pb2.FEAT_PWR:
            log.exception('Invalid Type: %d' % (msg.type))
        response = control_pb2.GetResponse()
        response.result = True
        response.value = control_pb2.POWER_UNK
        log.debug('Return %d' % response.value)
	return response

    def Set(self, msg):
        """Set the power status of a device.

        Arguments:
        msg: type control_pb2.SetRequest

	Returns:
        control_pb2.SetResponse
        """
        if msg.type != control_pb2.FEAT_PWR:
             log.exception('Invalid Type: %d' % (msg.type))
        self.cmd.append(PWR_COMMANDS[msg.value])

        log.debug('issuing %s' % (" ".join(self.cmd)))
        r = subprocess.call(self.cmd)
        response = control_pb2.GetResponse()
        response.result = (r == 0)
	return response


