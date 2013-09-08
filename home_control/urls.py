from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^home_control/', include('home_control.foo.urls')),
    url(r'^devices/$', 'control.views.devices'),
    url(r'^(?P<type>(devices|json))/(?P<device_id>\d+)/$', 'control.views.device'),
    url(r'^(?P<type>(devices|json))/(?P<device_id>\d+)/set$', 'control.views.set_device'),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
