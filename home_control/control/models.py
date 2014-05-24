from django.db import models
from django.utils import encoding
from lib.server.pb import control_pb2
from protobuf.socketrpc import RpcService
import logging

log = logging.getLogger(__name__)

FEATURE_TYPES = (
    (control_pb2.FEAT_PWR, u'Power Controller'),
    (control_pb2.FEAT_INPUT, u'Input Controller'),
    (control_pb2.FEAT_PERCENT, u'Percent Slider'),
)

STATES = (
    ('Power Controller', (
        (control_pb2.POWER_UNK, u'Unknown'),
        (control_pb2.POWER_ON, u'Power On'),
        (control_pb2.POWER_OFF, u'Power Off'))),
    ('Input Controller', (
        (control_pb2.INPUT_HDMI1, u'Input HDMI 1'),
        (control_pb2.INPUT_HDMI2, u'Input HDMI 2'),
        (control_pb2.INPUT_RGB, u'Input RGB'),
        (control_pb2.INPUT_SVIDEO, u'Input SVideo'),
        (control_pb2.INPUT_PC, u'Input PC'),
        (control_pb2.INPUT_CAMERA, u'Input Camcorder'),
        (control_pb2.INPUT_DVD, u'Input DVD'),
        (control_pb2.INPUT_Q, u'Input Q'),
        (control_pb2.INPUT_XBMC, u'Input XBMC'),
        (control_pb2.INPUT_PIANO, u'Input Piano'),
        (control_pb2.INPUT_CAST, u'Input Chromecast'))),
)

DEVICE_TYPES = (
    (control_pb2.DUMMY, u'For tests only'),
    (control_pb2.ROTEL, u'Rotel Receiver'),
    (control_pb2.EPSON, u'Epson Projector'),
    (control_pb2.APC, u'APC Power Controller'),
    (control_pb2.PC_WIN, u'Windows PC'),
    (control_pb2.PC_LINUX, u'Linux PC'),
    (control_pb2.X10, u'X10 Power Controller'),
    (control_pb2.UFO, u'UFO Power Controller'),
    (control_pb2.ANTHEM, u'Anthem Receiver'),
    (control_pb2.IPPOWER, u'IPPower Controller'),
)

class FeatureType(models.Model):
    value = models.IntegerField(choices=FEATURE_TYPES)
    def __unicode__(self):
         return self.get_value_display()

class State(models.Model):
    value = models.IntegerField(choices=STATES)
    def __unicode__(self):
         return self.get_value_display()

class DeviceType(models.Model):
    value = models.IntegerField(choices=DEVICE_TYPES)
    def __unicode__(self):
         return self.get_value_display()

class Feature(models.Model):
    name = models.CharField(max_length=30, blank=True)
    feature_type = models.ForeignKey(FeatureType)
    supported_states = models.ManyToManyField('State', blank=True)
    def __unicode__(self):
        if self.name:
            return self.name
        else:
            return unicode(self.feature_type) + ':' + ",".join([unicode(s) for s in self.supported_states.all()])

class DeviceClass(models.Model):
    device_type = models.ForeignKey(DeviceType)
    features = models.ManyToManyField('Feature', related_name='features')
    def __unicode__(self):
        return unicode(self.device_type) + ':' + ";".join([unicode(f) for f in self.features.all()])

class Location(models.Model):
    room = models.CharField(max_length=30)
    level = models.IntegerField()
    def __unicode__(self):
        return unicode(self.level) +    self.room

# Create your models here.
class Device(models.Model):
    name = models.CharField(max_length=30)
    device_class = models.ForeignKey(DeviceClass)
    server_name = models.CharField(max_length=30, blank=True)
    argument = models.CharField(max_length=30, blank=True)
    depends_on = models.ManyToManyField('Device', related_name='depends', symmetrical=False, blank=True)
    location = models.ForeignKey(Location)
    hidden = models.BooleanField(default=False)
    power_state = models.ForeignKey(State)
    def __unicode__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super(Device, self).__init__(*args, **kwargs)
        if not hasattr(self, 'device_class'):
            return
        c = self.device_class
        if c.device_type.value in [ control_pb2.APC, control_pb2.PC_WIN, control_pb2.PC_LINUX, control_pb2.UFO, control_pb2.IPPOWER ]:
            server = 'localhost'
        else:
            server = self.server_name
        self.service = RpcService(control_pb2.ControlService_Stub, 10021, server)
        d_pb = control_pb2.Device()
        d_pb.type = c.device_type.value
        d_pb.server = self.server_name
        d_pb.port = str(self.argument)
        self.pb = control_pb2.Device()
        self.pb.CopyFrom(d_pb)
    
    def send_get(self, feature_type):
        request = control_pb2.GetRequest()
        request.device.CopyFrom(self.pb)
        request.type = feature_type
        response = self.service.Get(request, timeout=10000)
        if not response.result:
            log.error('Invalide answer: ' + response.error)
        return response
    
    def send_set(self, feature_type, value):
        request = control_pb2.SetRequest()
        request.device.CopyFrom(self.pb)
        request.type = feature_type
        request.value = value
        response = self.service.Set(request, timeout=1000)
        if not response.result:
            log.error('Invalide answer: ' + response.error)
        return response

    def get_pwr(self):
        for d in self.depends_on.all():
            response = d.get_pwr()
            if response.value != control_pb2.POWER_ON:
                return response
        return self.send_get(control_pb2.FEAT_PWR)
    
    def send_pwr(self, value):
        # no protection for recursive dependencies.
        if value == control_pb2.POWER_ON:
            # power other device first
            for d in self.depends_on.all():
                 d.send_pwr(value)
        response = self.send_set(control_pb2.FEAT_PWR, value)
        if response.result:
            self.power_state = State.objects.get(value=value)
            self.save()
            if value == control_pb2.POWER_OFF:
                for d in self.depends_on.all():
                    d.send_pwr(value)
  
