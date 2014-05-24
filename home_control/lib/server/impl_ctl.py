"""Service Implemenation of the control protobuf"""

import logging
import os
import sys
from pb import control_pb2
if os.name != 'nt':
    import apc_ctl
import dummy_ctl
import epson_ctl
import pc_ctl
import rotel_ctl
import x10_ctl
import ufo_ctl
import anthem_ctl
import ippower_ctl

# Configure logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

DEVICE_OBJECT = {  control_pb2.DUMMY: dummy_ctl.DummyCtl,
                   control_pb2.ROTEL: rotel_ctl.RotelCtl,
                   control_pb2.EPSON: epson_ctl.EpsonCtl,
                   control_pb2.X10: x10_ctl.X10Ctl,
                   control_pb2.PC_WIN:  pc_ctl.PcCtl,
                   control_pb2.PC_LINUX:  pc_ctl.PcCtl,
                   control_pb2.UFO:  ufo_ctl.UfoCtl,
                   control_pb2.ANTHEM: anthem_ctl.AnthemCtl,
                   control_pb2.IPPOWER: ippower_ctl.IppowerCtl}

if os.name != 'nt':
    DEVICE_OBJECT[control_pb2.APC] = apc_ctl.ApcCtl

class ImplCtl(control_pb2.ControlService):
    @classmethod
    def _GetCtl(cls, device):
        try:
            ctl = DEVICE_OBJECT[device.type](device)
        except KeyError:
            raise NotImplementedError("%d type not implemented." % (device.type))
        return ctl

    def Get(self, controller, request, done):
      ctl = self._GetCtl(request.device)
      log.info('Receiving Get request for %s-%s' % (request.device.server, request.device.port))
      response = ctl.Get(request)
      done.run(response)

    def Set(self, controller, request, done):
      ctl = self._GetCtl(request.device)
      log.info('Receiving Set request for %s-%s' % (request.device.server, request.device.port))
      response = ctl.Set(request)
      done.run(response)
