#!/usr/bin/python

from crontab import CronTab
import datetime
from astral import Astral


city_name = 'San Francisco'
a = Astral()
a.solar_depression = 'civil'
city = a[city_name]
sun = city.sun(local=True)

print('Dawn:    %s' % str(sun['dawn']))
print('Sunrise: %s' % str(sun['sunrise']))
print('Noon:    %s' % str(sun['noon']))
print('Sunset:  %s' % str(sun['sunset']))
print('Dusk:    %s' % str(sun['dusk']))

# every week, update dawn
cron  = CronTab(user=True)

for event in ['sunrise', 'sunset']:
  event_time = sun[event].time()

  for job in cron.find_comment(event):
    job.hour.on(event_time.hour)
    job.minute.on(event_time.minute)
    print job

cron.write()
