# from control.models import Device
# from control.models import DeviceType
# from control.models import DeviceState
# from control.models import Location
# from django.contrib import admin
# 
# admin.site.register(DeviceType)
# admin.site.register(Location)
# admin.site.register(Device)

from control import models
from django.contrib import admin

admin.site.register(models.State)
admin.site.register(models.DeviceType)
admin.site.register(models.FeatureType)
admin.site.register(models.Feature)
admin.site.register(models.DeviceClass)
admin.site.register(models.Location)
admin.site.register(models.Device)
