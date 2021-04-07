"""
Coop

A simple yet complete program to manage and monitor your coop.

Configuration is done in the config.ini file.
Logging is done to the file specified in this config.ini file

"""

#TODO: Make 'door' run at every whole minute with something like 'if secondold is > second then do this ... secondold = second'.
#TODO: Make 'door' the main script
#TODO: Implement early-open time
#TODO: Put motor in one definition with variables
#TODO: Put status(led) in one definition with variables

import logging
import configparser
from datetime import datetime, timedelta, timezone
import RPi.GPIO as GPIO
import time
from suntime import Sun
import threading
#import urllib.request
#import pytz
import os

os.rename('/home/pi/coop.log', '/home/pi/'+datetime.now().strftime("%Y%m%d-%H%M%S")+'coop.log')

# config
config = configparser.ConfigParser()
config.read('/home/pi/coop/coop.ini')

# logging
logging.basicConfig(filename=config['Settings']['LogFile'], level=config['Settings']['LogLevel'],
                    format='%(asctime)s - %(levelname)s: %(message)s')

# Suntime
sun = Sun(float(config['Location']['Latitude']), float(config['Location']['Longitude']))
#tz = pytz.timezone('Europe/Berlin')
#now = (datetime.now(timezone.utc))
offsetclose = int(config['Door']['OffsetClose'])
offsetopen = int(config['Door']['OffsetOpen'])
#minopen = datetime.strptime(config['Door']['MinOpen'],'%H:%M')
#minopenlocal = tz.localize(minopen)
#minopenutc = minopenlocal.astimezone(pytz.utc)
#opentime = sun.get_sunrise_time() - timedelta(minutes=offsetopen)
#closetime = sun.get_sunset_time() + timedelta(minutes=offset)
#opentimetomorrow = sun.get_local_sunrise_time(datetime.now() + timedelta(days=1) - timedelta(minutes=offset))
#closetimeyesterday = sun.get_local_sunset_time(datetime.now() + timedelta(days=-1)) + timedelta(minutes=offset)
global stop_threads

#relais

# GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
MotorUp = int(config['GPIO']['ActUp'])
GPIO.setup(MotorUp, GPIO.OUT)
MotorDown = int(config['GPIO']['ActDwn'])
GPIO.setup(MotorDown, GPIO.OUT)
Relais = int(config['GPIO']['Relais'])
GPIO.setup(Relais, GPIO.OUT)
SwitchDown = int(config['GPIO']['BttnDwn'])
GPIO.setup(SwitchDown, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
SwitchUp = int(config['GPIO']['BttnUp'])
GPIO.setup(SwitchUp, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def button_callback(channel):
    if GPIO.input(channel):
        logging.debug( "Rising edge detected on %s", channel)
    else:
        logging.debug( "Falling edge detected on %s", channel)

def motor_up():
    logging.debug("motor_up")
    GPIO.output(MotorUp, GPIO.HIGH)
    GPIO.output(MotorDown, GPIO.LOW)

def motor_down():
    logging.debug("motor_down")
    GPIO.output(MotorDown, GPIO.HIGH)
    GPIO.output(MotorUp, GPIO.LOW)

def motor_stop():
    logging.debug("motor_stop")
    GPIO.output(MotorUp, GPIO.LOW)
    GPIO.output(MotorDown, GPIO.LOW)

def door():
    global door
    now = (datetime.now(timezone.utc))
    logging.debug("Time is: %s", now)
    logging.debug("Sunrise time today: %s", sun.get_sunrise_time())
    logging.debug("Sunset time today: %s", sun.get_sunset_time())
#    logging.debug("MinOpen time: %s", minopen)
#    logging.debug("MinOpenlocal time: %s", minopenlocal)
#    logging.debug("MinOpenutc time: %s", minopenutc))
    GPIO.add_event_detect(SwitchDown,GPIO.RISING,callback=button_callback, bouncetime=200)
    GPIO.add_event_detect(SwitchUp,GPIO.RISING,callback=button_callback, bouncetime=200)
    while True:
        now = (datetime.now(timezone.utc))
        minopen = datetime.strptime(datetime.now().strftime("%Y-%m-%d-")+config['Door']['MinOpen']+" +0000",'%Y-%m-%d-%H:%M %z')
        opentime = minopen if minopen > sun.get_sunrise_time() + timedelta(minutes=offsetopen) else sun.get_sunrise_time() + timedelta(minutes=offsetopen)
        closetime = sun.get_sunset_time() + timedelta(minutes=offsetclose)
        opentimetomorrow = minopen + timedelta(days=1) if sun.get_sunrise_time(datetime.now() + timedelta(days=1)) + timedelta(minutes=offsetopen) < minopen + timedelta(days=1) else sun.get_sunrise_time(datetime.now() + timedelta(days=1)) + timedelta(minutes=offsetopen)
        closetimeyesterday = sun.get_sunset_time(datetime.now() + timedelta(days=-1)) + timedelta(minutes=offsetclose)
        closetimetomorrow = sun.get_sunset_time(datetime.now() + timedelta(days=+1)) + timedelta(minutes=offsetclose)
        next_open = opentime if now < opentime else opentimetomorrow
        next_close = closetime if now < closetime else closetimetomorrow
        if GPIO.input(SwitchUp) == True:
            if door != "open":
                door = "open"
                logging.warning("Door status changed manually: %s", door)
                motor_up()
        elif GPIO.input(SwitchDown) == True:
            if door != "closed":
                motor_down()
                door = "closed"
                logging.warning("Door status changed manually: %s", door)
        elif opentime < now < closetime:
            if door != "open":
                motor_up()
                door = "open"
                logging.info("Door status changed: %s", door)
                logging.info("Closing scheduled at %s", next_close)
        elif closetimeyesterday < now < opentime or closetime < now < opentimetomorrow:
            if door != "closed":
                motor_down()
                door = "closed"
                logging.info("Door status changed: %s", door)
                logging.info("Opening scheduled at %s", next_open)

def relais():
#   possible options: door, inverse, time
    logging.debug("relais started")
    relais = config['Relais']['Mode']
    logging.debug("relais = %s", relais)
    global doornew
    global door
    doornew = "old"
    while True:
        if str(door) != str(doornew):
            doornew = str(door)
#        while True:
            if relais == "door":
                logging.info("relais set to 'door'")
                if door == "closed":
                    GPIO.output(Relais, GPIO.LOW)
                    logging.info("relais switched off")
                elif door == "open":
                    GPIO.output(Relais, GPIO.HIGH)
                    logging.info("relais switched on")
            elif relais == "inverse":
                logging.info("relais set to 'inverse'")
                if door == "closed":
                    GPIO.output(Relais, GPIO.HIGH)
                    logging.info("relais switched on")
                elif door == "open":
                    GPIO.output(Relais, GPIO.LOW)
                    logging.info("relais switched off")

def main_loop():
    while True:
        door()

if __name__ == "__main__":
    try:
#        t = threading.Thread(target=relais())
 #       t.start()
        door()
    except RuntimeError as error:
        print(error.args[0])
    except KeyboardInterrupt:
        print("\nExiting application\n")
        # exit the applications
        GPIO.cleanup()
