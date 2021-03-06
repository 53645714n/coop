from datetime import datetime, timezone, timedelta
from suntime import Sun, SunTimeException

latitude = 51.976132
longitude = 5.670997

sun = Sun(latitude, longitude)

# Get today's sunrise and sunset in UTC
today_sr = sun.get_local_sunrise_time()
today_ss = sun.get_local_sunset_time()
print('Today in Wageningen the sun rises at {} and sets at {}'.
      format(today_sr.strftime('%H:%M'), today_ss.strftime('%H:%M')))

# On a special date in your machine's local time zone
print(datetime.now())
print(sun.get_local_sunrise_time(datetime.now() + timedelta(days = 1)))
print(sun.get_local_sunset_time(datetime.now() + timedelta(days = -1)))

# Error handling (no sunset or sunrise on given location)
#latitude = 87.55
#longitude = 0.1
#sun = Sun(latitude, longitude)
#try:
#    abd_sr = sun.get_local_sunrise_time(abd)
#    abd_ss = sun.get_local_sunset_time(abd)
#    print('On {} at somewhere in the north the sun raised at {} and get down at {}.'.
#          format(abd, abd_sr.strftime('%H:%M'), abd_ss.strftime('%H:%M')))
#except SunTimeException as e:
#    print("Error: {0}.".format(e))
