"""Base class for controller"""

import sys
from pb import control_pb2

class BaseCtl:
    def __init__(self, device):
        """Initialize a controller for the time of the message.

        Arguments:
        device: type control_pb2.Device
        """
        
    def Get(self, msg):
        """Get the power status of a device.

        Arguments:
        msg: type control_pb2.GetPwrRequest

	Returns:
        control_pb2.GetPwrResponse
        """
        raise NotImplementedError("Get Power not supported")

    def Set(self, msg):
        """Set the power status of a device.

        Arguments:
        msg: type control_pb2.SetPwrRequest

	Returns:
        control_pb2.SetPwrResponse
        """
        raise NotImplementedError("Set Power not supported")

