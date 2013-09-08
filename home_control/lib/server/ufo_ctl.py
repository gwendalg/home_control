"""Class for UFO [Visible Energy] controller.

http://portal.visiblenergy.com/index.php/page/articles.html/_/developers/local-http-api
"""

import logging
import re
import sys
import base_ctl
import urllib2
from xml.dom.minidom import parseString
from pb import control_pb2

# Configure logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Default Value. No way to update them yet.
PWR_COMMANDS = { control_pb2.POWER_ON: {'in': 'ON', 'out': 'on'},
                 control_pb2.POWER_OFF: {'in': 'OFF', 'out': 'off'}}

class UfoCtl(base_ctl.BaseCtl):
    def __init__(self, device):
        """Initialize a controller for the time of the message.

        Arguments:
        device: type control_pb2.Device
        """
        self.urlbase="http://%s" % '/'.join([device.server, device.port])

    @classmethod
    def getText(cls, nodelist):
      rc = []
      for node in nodelist:
          if node.nodeType == node.TEXT_NODE:
              rc.append(node.data)
      return ''.join(rc)

    def _get(self):       
        url = self.urlbase + "/status.xml"
        try:
          request = urllib2.urlopen(url,timeout=2)
        except urllib2.URLError as e:
          print "Unable to access %s: %s" % (url, e)
          return control_pb2.POWER_UNK
        dom = parseString(request.read())
        state = dom.getElementsByTagName("state")[0]
        value = self.getText(state.childNodes)
        for k, v in PWR_COMMANDS.iteritems():
          if value == v['in']:
            return k
        return control_pb2.POWER_UNK
        
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
        response.value = self._get()
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
        url = self.urlbase + "/set.xml?value=" + PWR_COMMANDS[msg.value]['out']
        try:
          request = urllib2.urlopen(url,timeout=2)
        except urllib2.URLError as e:
          print "Unable to access %s: %s" % (url, e)
        response = control_pb2.GetResponse()
        response.result = True
	return response

test_str="""\
<strip mac="0012EB">
<status state="ONLINE">
<socket position="0">
<state>OFF</state>
<watts>0.00</watts>
<peak>118.00</peak>
<role type="neutral"/>
<timers total="0"/>
<oneshottimers total="0"/>
</socket>
</status>
</strip>
"""
