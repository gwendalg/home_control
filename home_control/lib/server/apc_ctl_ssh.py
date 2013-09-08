"""Class for APC controller"""

import logging
import pexpect
import re
import sys
import base_ctl
from pb import control_pb2

# Configure logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Default Value. No way to update them yet.
USER='annie'
PASSWD='love'
PWR_COMMANDS = { control_pb2.POWER_ON: {'in': 'ON', 'out': '1'},
                 control_pb2.POWER_OFF: {'in': 'OFF', 'out': '2'}}

class ApcCtl(base_ctl.BaseCtl):
    def __init__(self, device):
        """Initialize a controller for the time of the message.

        Arguments:
        device: type control_pb2.Device
        """
        id = '@'.join([USER, device.server])
        self.cursor = '\n> '
        value_re = re.compile(r'(?P<value_string>(ON|OFF))')
        self.get_value = control_pb2.POWER_UNK
        self.child = pexpect.spawn(command='ssh', args=['-vv', id], timeout=60, logfile=sys.stdout)
        self.child.expect(id + '\'s password:')
        self.child.sendline(PASSWD + '\r')
        # The menus to go through:
        # Control Console
        # Device Manager
        # Outlet Management
        # Outlet Control/Configuration
	for c in [ 1, 2, 1, device.port]:
            self.child.expect(self.cursor)
            self.child.sendline(str(c) + '\r')
        self.child.expect('State        : ')
        line = self.child.readline()
        log.debug('line: %s' % (line))
        result = value_re.match(line)
        if result:
            for k, v in PWR_COMMANDS.iteritems():
                if result.group('value_string') == v['in']:
                    self.get_value = k
        
    def __del__(self):
        """ Clean the connection for the next call."""
	for _ in xrange(4):
            self.child.expect(self.cursor)
            self.child.send('\033')
        self.child.expect(self.cursor)
        self.child.sendline('4\r')
        self.child.close()
       
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
        response.value = self.get_value
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
        log.debug('Got %d' % msg.value)
	if self.get_value != msg.value:
            self.get_value = msg.value
            self.child.expect(self.cursor)
            self.child.sendline(PWR_COMMANDS[msg.value]['out'] + '\r')
            self.child.expect('Enter \'YES\' to continue or <ENTER> to cancel : ')
            self.child.sendline('YES\r')
            self.child.expect('Press <ENTER> to continue...')
            self.child.sendline('\r')
        response = control_pb2.GetResponse()
        response.result = True
	return response


