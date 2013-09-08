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
logging.basicConfig(level=logging.DEBUG)

# Rotel RSX-1056 RS232 HEX Protocol
ROTEL_RSX_1056_ID = 0xC5
# ESC/VP21 Command Users Guide for Business Projectors
ROTEL_PORT_VALUE={ control_pb2.INPUT_PC: { 'in': 'PC', 'out': [ 0x10, 0x05]},
                   control_pb2.INPUT_DVD: { 'in': 'DYD', 'out': [ 0x10, 0x06]},
                   control_pb2.INPUT_CAMERA: { 'in': 'CD', 'out': [ 0x10, 0x09]},
                   control_pb2.INPUT_Q : { 'in': 'Q', 'out': [ 0x10, 0x07]},
                   control_pb2.POWER_OFF: { 'in': 'invalid', 'out': [ 0x10, 0x4A]},
                   control_pb2.POWER_ON: { 'in': 'invalid', 'out':  [ 0x10, 0x4B]}}

ROTEL_REFRESH_DISPLAY = [ 0x10, 0xFF]
ROTEL_SM_OUT_MSG = 0
ROTEL_SM_HDR = 1
ROTEL_SM_LEN = 2
ROTEL_SM_ID = 3
ROTEL_SM_PLY = 4


class RotelCtl(base_ctl.BaseCtl):
    def __init__(self, device):
        # default are fine: 
        # Select RS-232C at Advanced Setting of the Menu.
        # Communication condition
        # Baud rate
        # : 19200bps
        # Data length
        # : 8 bits
        # Parity
        # : No
        # Stop bit
        # : 1 bit
        # Flow control
        # : No
        try:
            self.serial = serial.serial_for_url(device.port, baudrate=19200, timeout=1, writeTimeout=1)
        except serial.SerialException as e:
            print "Unable to open serial port %s to Epson Projector: %s" % (port, e)
        self.rotel_id = ROTEL_RSX_1056_ID
        self.sm = ROTEL_SM_OUT_MSG
        self.payload = ''
        self.volume = 0
        self.source = ''

    @classmethod
    def avoid_header(cls, value):
        if value[0] == 0xFD or value[0] == 0xFE:
          return [0xFD, value[0] - 0xFD]
        else:
          return value

    def build_command(self, value):
        res = [ self.rotel_id ]
        cksum = 0xFF + self.rotel_id
        for v in value:
          byte = self.avoid_header([v])
          for b in byte:
            res.append(b)
            cksum += b
        res.insert(0, len(res))
        cksum += len(res)
        res.extend(self.avoid_header([cksum & 0xFF]))
        return res

    def command(self, value):
        res = [0xFE]
        res.extend(self.build_command(value))
        return "".join(chr(d) for d in res)

    def reader(self):
        self.payload = ''
        while 1:
            s = self.serial.read(1)
            if not s:
                break
            c = ord(s[0])
            #log.debug("cmd: %s - %d" % (hex(c), self.sm))
            if self.sm == ROTEL_SM_OUT_MSG:
                 if c == 0xFE:
                      self.sm = ROTEL_SM_HDR
            elif self.sm == ROTEL_SM_HDR:
                 count = c - 2 # ID and Command
                 self.sm = ROTEL_SM_LEN
            elif self.sm == ROTEL_SM_LEN:
                 if c == self.rotel_id:
                     # We are only interested in Refresh display
                     self.sm = ROTEL_SM_ID
                 else:
                     self.sm = ROTEL_SM_OUT_MSG 
            elif self.sm == ROTEL_SM_ID:
                 if c == 0x20:
                     # We are only interested in Refresh display
                     self.sm = ROTEL_SM_PLY
                 else:
                     self.sm = ROTEL_SM_OUT_MSG 
            elif self.sm == ROTEL_SM_PLY:
                 self.payload += s
                 count -= 1
                 if count == 0:
                     self.sm = ROTEL_SM_OUT_MSG 

    def check_command(self, command):
        self.response_thread = threading.Thread(target=self.reader)
        self.response_thread.setDaemon(True)
        self.response_thread.start()
        cmd = self.command(command)
        log.debug("cmd: %s" % (" ".join([hex(ord(c)) for c in cmd])))
        self.serial.write(cmd)
        self.response_thread.join()
        log.debug("rsp: %s" % (self.payload[0:13]))
        if self.payload:
            self.source = self.payload[0:10].strip()
            s = self.payload[10:13].strip()
            if s.isdigit():
                log.debug("volume: %s" % (" ".join([hex(ord(c)) for c in s])))
                self.volume = int(s)
            return True
        else:
            return False

    def Get(self, request):
        response = control_pb2.GetResponse()
        rc = self.check_command(ROTEL_REFRESH_DISPLAY)
        if request.type == control_pb2.FEAT_PWR:
            response.result = True
            if rc and self.source.isalnum():
                response.value = control_pb2.POWER_ON
            else:
                response.value = control_pb2.POWER_OFF
        elif request.type == control_pb2.FEAT_INPUT:
            response.result = rc
            for k, v in ROTEL_PORT_VALUE.iteritems():
                if self.source == v['in']:
                    response.value = k
                    break;
        elif request.type == control_pb2.FEAT_PERCENT:
            response.result = rc
            response.percent = self.volume
        else:
            response.result = False
            response.error = "Unknown Command"
        return response

    def Set(self, request):
        response = control_pb2.SetResponse()
        response.result = True
        if request.type == control_pb2.FEAT_PERCENT:
             if request.percent > 96:
                 request.percent = 96
             self.serial.write(self.command([0x30, request.percent]))
        else:
            try:
                self.serial.write(self.command(ROTEL_PORT_VALUE[request.value]['out']))
            except KeyError:
                response.error = "Unknown Input %d" % (request.value)
                response.result = False
        return response


