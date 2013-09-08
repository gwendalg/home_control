"""Class for PC controller - client side"""

import logging
import subprocess
import sys
import base_ctl
from pb import control_pb2

# Configure logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class PcCtl(base_ctl.BaseCtl):
    COUNT = 3

    def __init__(self, device):
        """Initialize a controller for the time of the message.

        Arguments:
        device: type control_pb2.Device
        """
        self.device = device

    def ping(self, timeout):
        r = subprocess.call(['ping', '-c', str(self.COUNT), '-q', '-w', str(timeout), self.device.server])
        if r == 0:
            return control_pb2.POWER_ON
        else:
            return control_pb2.POWER_OFF

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
        response.value = self.ping(5)

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
        if msg.value == control_pb2.POWER_ON:
            subprocess.call(['wakeonlan', self.device.port])
            timeout = 60
        else:
            timeout = 10

        response = control_pb2.GetResponse()
        response.result = (self.ping(timeout) == msg.value)
	return response


