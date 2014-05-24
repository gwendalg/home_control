"""Class for UFO [Visible Energy] controller.

http://portal.visiblenergy.com/index.php/page/articles.html/_/developers/local-http-api
"""

import logging
import re
import sys
import base_ctl
import urllib2
from pb import control_pb2

# Configure logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class IppowerCtl(base_ctl.BaseCtl):
    def __init__(self, device):
        """Initialize a controller for the time of the message.

        ipower controller:
        get
        http://admin:12345678@192.168.1.57/Set.cmd?CMD=GetPower
        returns:
        P60=0,P61=1,P62=1,P63=1,P64=0,P65=0,P66=0,P67=0

        set
        http://admin:12345678@192.168.1.57/Set.cmd?CMD=SetPower+P60=0

        Arguments:
        device: type control_pb2.Device
        """
        self._get_urlbase="http://admin:12345678@%s/Set.cmd?CMD=GetPower" % (device.server)
        self._set_urlbase="http://admin:12345678@%s/Set.cmd?CMD=SetPower+P%d=" % (device.server, 59 + device.port)
        self.device = device

    @classmethod
    def getText(cls, nodelist):
      rc = []
      for node in nodelist:
          if node.nodeType == node.TEXT_NODE:
              rc.append(node.data)
      return ''.join(rc)

    def _get(self):
        url = self._get_urlbase
        try:
          request = urllib2.urlopen(url,timeout=2)
        except urllib2.URLError as e:
          print "Unable to access %s: %s" % (url, e)
          return control_pb2.POWER_UNK
        value = request.read().split(',')[self.device.port - 1].split('=')[1]
        return control_pb2.POWER_OFF - value

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
        url = self._set_urlbase + str(control_pb2.POWER_OFF - PWR_COMMANDS[msg.value])
        try:
          request = urllib2.urlopen(url,timeout=2)
        except urllib2.URLError as e:
          print "Unable to access %s: %s" % (url, e)
        response = control_pb2.GetResponse()
        response.result = True
        return response
