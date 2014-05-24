"""Class for IPPower controller.

"""

import logging
import re
import sys
import base_ctl
import requests
from HTMLParser import HTMLParser
from pb import control_pb2

# Configure logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class IppowerParser(HTMLParser):
    def __init__(self, port):
        HTMLParser.__init__(self)
        self.port = port
        self.status = []

    def handle_data(self, data):
        log.debug('Return %d: %s' % (self.port, data))
        self.status.extend(data.split(','))

    def get_port(self):
        return int(self.status[self.port - 1].split('=')[1]) 

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
        self.port = int(device.port)
        self.auth = ('admin', '12345678')
        
        self.urlbase="http://%s/Set.cmd" % (device.server)

    def _get(self):
        userdata = { "CMD" : "GetPower" }
        try:
          resp = requests.get(self.urlbase, params=userdata, auth=self.auth)
        except requests.exceptions.ConnectionError as e:
          print "Unable to access %s: %s" % (self.urlbase, e)
          return control_pb2.POWER_UNK
        parser = IppowerParser(self.port)
        parser.feed(resp.text)
        return control_pb2.POWER_OFF - parser.get_port()

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
        url=self.urlbase + '?CMD=SetPower+P%d=%d' % (59 + self.port, control_pb2.POWER_OFF - msg.value)
        try:
          resp = requests.get(url, auth=self.auth)
        except requests.exceptions.ConnectionError as e:
          print "Unable to access %s: %s" % (self.urlbase, e)
        parser = IppowerParser(self.port)
        parser.feed(resp.text)
        response = control_pb2.GetResponse()
        response.result = True
        return response
