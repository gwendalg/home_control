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
ANTHEM_PORT_VALUE={ control_pb2.INPUT_PC: 1,
                    control_pb2.INPUT_DVD: 2,
                    control_pb2.INPUT_TV: 3}

ANTHEM_PWR_VALUE={ control_pb2.POWER_OFF: 0,
                   control_pb2.POWER_ON: 1}

ANTHEM_COMMANDS = { control_pb2.FEAT_PWR: ['P1P', ANTHEM_PWR_VALUE, 10],
                    control_pb2.FEAT_INPUT: ['P1S', ANTHEM_PORT_VALUE, 2] }

class AnthemCtl(base_ctl.BaseCtl):
    def __init__(self, device):
        # default are fine: 
        # Select RS-232C at Advanced Setting of the Menu.
        # Communication condition
        # Baud rate
        # : 115200ps
        # Data length
        # : 8 bits
        # Parity
        # : No
        # Stop bit
        # : 1 bit
        # Flow control
        # : Software
        try:
            self.serial = serial.serial_for_url(device.port, baudrate=115200, xonxoff=True, timeout=5, writeTimeout=1)
        except serial.SerialException as e:
            log.error('Unable to open serial port %s to Anthem Projector: %s' % (device.port, e))
        self.response_buffer = ""
        self.response_buffer_size = 0
        
    def reader(self):
        self.response_buffer = self.serial.read(self.response_buffer_size)
        log.debug('buffer:---%s---' % (self.response_buffer))

    def Checkcommand(self, command, padding):
        self.response_buffer_size = padding + len(command) + 2   # response + CR
        self.response_thread = threading.Thread(target=self.reader)
        self.response_thread.setDaemon(True)
        self.response_thread.start()
        self.serial.write("%s?;" % (command))
        self.response_thread.join()
        
        m = re.match(r".*%s(?P<cmd>\d{1}).*" % (command),
                     self.response_buffer, re.DOTALL)
        if m:
          return int(m.group('cmd'),10)
        else:
          return None

    def GetCommand(self, command):
        response = control_pb2.GetResponse()
        for _ in xrange(0,3):
          rc = self.Checkcommand(command[0], 0)
          if rc is None:
            time.sleep(command[2])
          else:
            break
        if rc is None:
          response.result = False
          response.error = "No communication"
          return response
        for k, v in command[1].iteritems():
          if rc == v:
            response.result = True
            response.value = k
            return response
        response.result = False
        response.error = "Invalid response %d" % (rc)
        return response

    def Get(self, request):
        return self.GetCommand(ANTHEM_COMMANDS[request.type])

    def Set(self, request):
        command = ANTHEM_COMMANDS[request.type]
        for _ in xrange(0,3):
          self.serial.write("%s%s;" % (command[0], command[1][request.value]))
          time.sleep(command[2])
          rc = self.Checkcommand(command[0], 1)
          if rc == command[1][request.value]:
            break
        return self.GetCommand(command) 
