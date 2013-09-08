"""Class for APC controller"""

import logging
import sys
import base_ctl
from pb import control_pb2
from pysnmp import debug
from pysnmp.proto import rfc1902
from pysnmp.entity.rfc3413.oneliner import cmdgen

# Configure logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
#debug.setLogger(debug.Debug('all'))

PWR_COMMANDS = { control_pb2.POWER_ON: 1,
                 control_pb2.POWER_OFF: 2}

SNMP_UDP_PORT = 161
# pysnmp does not like the new MIB
# The variable is found with
#  snmpget -v1 -c public -ObentU apcgwen PowerNet-MIB::sPDUOutletCtl.1
# SNMP_APC_MIB = 'PowerNet-MIB'
# SNMP_APC_PORT_VAR = 'sPDUOutletCtl'
SNMP_APC_PORT_VAR = '.1.3.6.1.4.1.318.1.1.4.4.2.1.3.'
SNMP_APC_USER = 'pistring'


class ApcCtl(base_ctl.BaseCtl):
    def __init__(self, device):
        """Initialize a controller for the time of the message.

        Arguments:
        device: type control_pb2.Device
        """
        self.cmdGen = cmdgen.CommandGenerator()
        self.device = device
       
    @classmethod
    def _CheckResponseOk(cls, response, errorIndication, errorStatus, errorIndex, varBinds):
        """ Check for errors and print out results """
        if errorIndication:
            response.result = False
            response.error = errorIndication
        elif errorStatus:
            response.result = False
            response.error = ('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex)-1] or '?'
                )
            )
        else:
           response.result = True
        return response.result

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
        errorIndication, errorStatus, errorIndex, varBinds = self.cmdGen.getCmd(
            cmdgen.CommunityData(SNMP_APC_USER, mpModel=0),
            cmdgen.UdpTransportTarget((self.device.server, SNMP_UDP_PORT)),
            cmdgen.MibVariable(SNMP_APC_PORT_VAR + str(self.device.port))
        )
        
        if self._CheckResponseOk(response, errorIndication, errorStatus, errorIndex, varBinds):
            assert(len(varBinds) == 1)
            val = varBinds[0][1]
            for k, v in PWR_COMMANDS.iteritems():
                if val == v:
                    response.value = k
                response.result = True
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
        errorIndication, errorStatus, errorIndex, varBinds = self.cmdGen.setCmd(
            cmdgen.CommunityData(SNMP_APC_USER, mpModel=0),
            cmdgen.UdpTransportTarget((self.device.server, SNMP_UDP_PORT)),
            (SNMP_APC_PORT_VAR + str(self.device.port), rfc1902.Integer(PWR_COMMANDS[msg.value]))
        )
        response = control_pb2.GetResponse()
        self._CheckResponseOk(response, errorIndication, errorStatus, errorIndex, varBinds)
	return response


