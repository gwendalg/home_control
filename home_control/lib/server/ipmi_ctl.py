"""Class for IPMI controller - client side"""

import logging
import subprocess
import sys
import base_ctl
from pb import control_pb2

# Configure logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

PWR_COMMANDS = { control_pb2.POWER_ON: ['--on', '--wait-until-on'],
                 control_pb2.POWER_OFF: ['--soft', '--wait-until-off'] }

class IpmiCtl(base_ctl.BaseCtl):
    COUNT = 3

    def __init__(self, device):
        """Initialize a controller for the time of the message.

        Arguments:
        device: type control_pb2.Device
        """
        self.device = device
	self.cmd = ['ipmipower', '--host', self.device.server, '--username', 'admin', '--password', 'admin']
        self.PWR_RESULTS = { self.device.server + ': on\n': control_pb2.POWER_ON,
                             self.device.server + ': off\n' : control_pb2.POWER_OFF }
        self.OK = self.device.server + ': ok\n'


    def ipmi_cmd(self, function):
        p = subprocess.Popen(self.cmd + function, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result,err = p.communicate()
        r = p.returncode
        if r == 0:
            return (r,result)
        else:
            return (r,err)

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
	rc, result = self.ipmi_cmd(['--stat'])
	if rc == 0:
            response.result = True
            response.value = self.PWR_RESULTS[result]
        else:
            response.result = False
            response.error = result

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
        rc, result = self.ipmi_cmd(PWR_COMMANDS[msg.value])
        response = control_pb2.GetResponse()
        if rc == 0 and result == self.OK:
            response.result = True
            response.value = msg.value
        else:
            response.result = False
            response.error = result

	return response


