import logging
import os
import serial
import sys
import re
import time
import threading
import base_ctl
from pb import control_pb2

# Configure logging
log = logging.getLogger(__name__)


# ESC/VP21 Command Users Guide for Business Projectors
EPSON_PORT_VALUE={control_pb2.INPUT_COMPONENT: { 'in': '1F', 'out': [0x1F]},
                  control_pb2.INPUT_HDMI1: { 'in': '30', 'out': [0x30]},
                  control_pb2.INPUT_HDMI2: { 'in': 'A0', 'out': [0xA0]},
                  control_pb2.INPUT_RGB: { 'in': '21', 'out': [0x21]},
                  control_pb2.INPUT_SVIDEO: { 'in': '42', 'out': [0x42]},
                  control_pb2.POWER_OFF: { 'in': 'OFF', 'out': [0, 3, 4]},
                  control_pb2.POWER_ON: { 'in': 'ON', 'out': [1, 2]}}

EPSON_COMMANDS = { control_pb2.FEAT_PWR: 'PWR',
                   control_pb2.FEAT_INPUT: 'SOURCE' }

EPSON_DELAYS = { control_pb2.FEAT_PWR: 60,
                 control_pb2.FEAT_INPUT: 5 }

class EpsonCtl(base_ctl.BaseCtl):
    def __init__(self, device):
        # default are fine: 
        # Select RS-232C at Advanced Setting of the Menu.
        # Communication condition
        # Baud rate
        # : 9600bps
        # Data length
        # : 8 bits
        # Parity
        # : No
        # Stop bit
        # : 1 bit
        # Flow control
        # : No
        try:
            self.serial = serial.serial_for_url(device.port, timeout=5, writeTimeout=1)
        except serial.SerialException as e:
            log.error('Unable to open serial port %s to Epson Projector: %s' % (device.port, e))
        self.response_buffer = ""
        self.response_buffer_size = 0
        
    def reader(self):
        self.response_buffer = self.serial.read(self.response_buffer_size)
        log.debug('buffer: %s' % (self.response_buffer))


    def Checkcommand(self, command):
        self.response_buffer_size = 1 + max(len("ERR:"), len("%s=xx:" % (command)))
        self.response_thread = threading.Thread(target=self.reader)
        self.response_thread.setDaemon(True)
        self.response_thread.start()
        self.serial.write("%s?\r" % (command))
        self.response_thread.join()
        
        m = re.match(r".*%s=(?P<cmd>\w{2}).*" % (command), self.response_buffer)
        if m:
          return int(m.group('cmd'), 16)
        else:
          return None

    def Checkerror(self):
        return self.Checkcommand("ERR")

    def GetCommand(self, command):
        response = control_pb2.GetResponse()
        rc = self.Checkcommand(command)
        if rc is None:
          response.result = False
          response.error = "No communication"
          return response
        for k, v in EPSON_PORT_VALUE.iteritems():
          if rc in v['out']:
            response.result = True
            response.value = k
            return response
        response.result = False
        response.error = "Invalid response 0x%2x" % (rc)
        return response

    def Get(self, request):
        send_buffer = "%s?\r" % (EPSON_COMMANDS[request.type])
        log.debug('send: %s' % (send_buffer))
        self.serial.write(send_buffer)
        return self.GetCommand(EPSON_COMMANDS[request.type])

    def SetCommand(self, request, command, timeout):
        send_buffer = "%s %s\r" % (command, EPSON_PORT_VALUE[request.value]['in'])
        log.debug('send: %s' % (send_buffer))
        self.serial.write(send_buffer)
        delay = max(timeout / 10, 1)
        time.sleep(1)
        for _ in xrange(0, timeout, delay):
          response = self.GetCommand(command)
          if response.result:
              break;
          time.sleep(delay)
        if not response.result:
          response.error = "Device Timeout"
        return response

    def Set(self, request):
        while True:
            temp_rsp = self.SetCommand(request,
                                       EPSON_COMMANDS[request.type],
                                       EPSON_DELAYS[request.type])
            response = control_pb2.SetResponse()
            response.result = temp_rsp.result
            if temp_rsp.error:
                response.error = temp_rsp.error
                break
            if temp_rsp.value == request.value:
                break
            time.sleep(1)
        return response
