# Create your views here.
from django.http import Http404
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.utils import simplejson
from control.models import Device
from control.models import Feature
from control.models import FeatureType
from control.models import State
from lib.server.pb import control_pb2
import logging

log = logging.getLogger(__name__)

def devices(request):
    devices = [{ 'device': d, 'location': d.location } for d in Device.objects.filter(hidden=False).order_by('location', 'name')]
    return render_to_response('home_control/devices.html', {'devices': devices})

def device(request, type, device_id):
    try:
        d = Device.objects.get(pk=device_id)
    except Device.DoesNotExist:
        raise Http404
    c = d.device_class

    features = {}
    response_pwr = None
    pwr_feature_type = FeatureType.objects.filter(value=control_pb2.FEAT_PWR)
    for p in c.features.filter(feature_type=pwr_feature_type):
        response_pwr = d.get_pwr()
        features[p] = dict([(s, s.value == response_pwr.value) for s in p.supported_states.all()])
   
    if (not response_pwr or 
        response_pwr.value == control_pb2.POWER_ON or
        d.power_state.value == control_pb2.POWER_ON):
        for p in c.features.exclude(feature_type=pwr_feature_type):
            response = d.send_get(p.feature_type.value)
            features[p] = dict([(s, s.value == response.value) for s in p.supported_states.all()])
    if type == 'devices':
        return render_to_response('home_control/device_page.html',
                                  {'device': d, 'features': features},
                                  context_instance = RequestContext(request))
    else:
        response_data = {}
        response_data['device'] = d
        response_data['features'] = features
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")

def set_device(request, type, device_id):
    """Handler of forms. Only one event at time."""
    feature_id, value = request.GET.items()[0]
    try:
        d = Device.objects.get(pk=device_id)
    except Device.DoesNotExist:
        raise Http404
    try:
        f = Feature.objects.get(pk=feature_id)
    except Feature.DoesNotExist:
        raise Http404
    if f.feature_type.value == control_pb2.FEAT_PWR:
        d.send_pwr(int(value))
    else:
        d.send_set(f.feature_type.value, int(value))
    return render_to_response('home_control/device_set.html')
