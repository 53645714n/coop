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
import os

# config
config = configparser.ConfigParser()
config.read('/home/pi/coop/coop.ini')

# logging
logfile = config['Settings']['LogFile']
os.rename(logfile, '/home/pi/'+datetime.now().strftime("%Y%m%d-%H%M%S")+'.log') if os.path.isfile(logfile) else print('no logfile found, first time run?')
logging.basicConfig(filename=logfile, level=config['Settings']['LogLevel'],format='%(asctime)s - %(levelname)s: %(message)s') if logfile != "" else logging.basicConfig(level=config['Settings']['LogLevel'],format='%(asctime)s - %(levelname)s: %(message)s')

# Suntime
sun = Sun(float(config['Location']['Latitude']), float(config['Location']['Longitude']))
offsetclose = int(config['Door']['OffsetClose'])
offsetopen = int(config['Door']['OffsetOpen'])
global stop_threads


# GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
MotorUp = int(config['GPIO']['ActUp'])
GPIO.setup(MotorUp, GPIO.OUT)
MotorDown = int(config['GPIO']['ActDwn'])
GPIO.setup(MotorDown, GPIO.OUT)
Relais = int(config['GPIO']['Relais'])
GPIO.setup(Relais, GPIO.OUT)
RelaisOn = int(config['GPIO']['RelaisOn'])
GPIO.setup(RelaisOn, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
RelaisOff = int(config['GPIO']['RelaisOff'])
GPIO.setup(RelaisOff, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
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

def door():
    global door
    now = (datetime.now(timezone.utc))
    logging.debug("Time is: %s", now)
    logging.debug("Sunrise time today: %s", sun.get_sunrise_time())
    logging.debug("Sunset time today: %s", sun.get_sunset_time())
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
        elif stop_threads:
            break

def relais():
    global relaisstatus
    relaisstatus = "undefined"
    logging.debug("relais started")
    relais = config['Relais']['Mode']
    logging.info("Relais set to mode: %s", relais)
    GPIO.add_event_detect(RelaisOn,GPIO.RISING,callback=button_callback, bouncetime=200)
    GPIO.add_event_detect(RelaisOff,GPIO.RISING,callback=button_callback, bouncetime=200)
    while True:
        if relais == "door":
            now = (datetime.now(timezone.utc))
            minopen = datetime.strptime(datetime.now().strftime("%Y-%m-%d-")+config['Door']['MinOpen']+" +0000",'%Y-%m-%d-%H:%M %z')
            opentime = minopen if minopen > sun.get_sunrise_time() + timedelta(minutes=offsetopen) else sun.get_sunrise_time() + timedelta(minutes=offsetopen)
            closetime = sun.get_sunset_time() + timedelta(minutes=offsetclose)
            opentimetomorrow = minopen + timedelta(days=1) if sun.get_sunrise_time(datetime.now() + timedelta(days=1)) + timedelta(minutes=offsetopen) < minopen + timedelta(days=1) else sun.get_sunrise_time(datetime.now() + timedelta(days=1)) + timedelta(minutes=offsetopen)
            closetimeyesterday = sun.get_sunset_time(datetime.now() + timedelta(days=-1)) + timedelta(minutes=offsetclose)
            closetimetomorrow = sun.get_sunset_time(datetime.now() + timedelta(days=+1)) + timedelta(minutes=offsetclose)
            next_open = opentime if now < opentime else opentimetomorrow
            next_close = closetime if now < closetime else closetimetomorrow
            if GPIO.input(RelaisOn) == True:
                if relaisstatus != "on":
                    GPIO.output(Relais,GPIO.HIGH)
                    relaisstatus = "on"
                    logging.warning("Relais status changed manually: %s", relaisstatus)
            elif GPIO.input(RelaisOff) == True:
                if door != "off":
                    GPIO.output(Relais,GPIO.LOW)
                    relaisstatus = "off"
                    logging.warning("Relais status changed manually: %s", relaisstatus)
            elif opentime < now < closetime:
                if relaisstatus != "on":
                    GPIO.output(Relais,GPIO.HIGH)
                    relaisstatus = "on"
                    logging.info("Relais status changed: %s", relaisstatus)
            elif closetimeyesterday < now < opentime or closetime < now < opentimetomorrow:
                if relaisstatus != "off":
                    GPIO.output(Relais,GPIO.LOW)
                    relaisstatus = "off"
                    logging.info("Relais status changed: %s", relaisstatus)
        elif relais == "inverse":
            now = (datetime.now(timezone.utc))
            minopen = datetime.strptime(datetime.now().strftime("%Y-%m-%d-")+config['Door']['MinOpen']+" +0000",'%Y-%m-%d-%H:%M %z')
            opentime = minopen if minopen > sun.get_sunrise_time() + timedelta(minutes=offsetopen) else sun.get_sunrise_time() + timedelta(minutes=offsetopen)
            closetime = sun.get_sunset_time() + timedelta(minutes=offsetclose)
            opentimetomorrow = minopen + timedelta(days=1) if sun.get_sunrise_time(datetime.now() + timedelta(days=1)) + timedelta(minutes=offsetopen) < minopen + timedelta(days=1) else sun.get_sunrise_time(datetime.now() + timedelta(days=1)) + timedelta(minutes=offsetopen)
            closetimeyesterday = sun.get_sunset_time(datetime.now() + timedelta(days=-1)) + timedelta(minutes=offsetclose)
            closetimetomorrow = sun.get_sunset_time(datetime.now() + timedelta(days=+1)) + timedelta(minutes=offsetclose)
            next_open = opentime if now < opentime else opentimetomorrow
            next_close = closetime if now < closetime else closetimetomorrow
            if GPIO.input(RelaisOn) == True:
                if relaisstatus != "on":
                    GPIO.output(Relais,GPIO.HIGH)
                    relaisstatus = "on"
                    logging.warning("Relais status changed manually: %s", relaisstatus)
            elif GPIO.input(RelaisOff) == True:
                if door != "off":
                    GPIO.output(Relais,GPIO.LOW)
                    relaisstatus = "off"
                    logging.warning("Relais status changed manually: %s", relaisstatus)
            elif opentime < now < closetime:
                if relaisstatus != "off":
                    GPIO.output(Relais,GPIO.LOW)
                    relaisstatus = "off"
                    logging.info("Relais status changed: %s", relaisstatus)
            elif closetimeyesterday < now < opentime or closetime < now < opentimetomorrow:
                if relaisstatus != "on":
                    GPIO.output(Relais,GPIO.HIGH)
                    relaisstatus = "on"
                    logging.info("Relais status changed: %s", relaisstatus)
        elif relais == "manual":
            if GPIO.input(RelaisOn) == True:
                if relaisstatus != "on":
                    GPIO.output(Relais,GPIO.HIGH)
                    relaisstatus = "on"
                    logging.warning("Relais status changed manually: %s", relaisstatus)
            elif GPIO.input(RelaisOff) == True:
                if door != "off":
                    GPIO.output(Relais,GPIO.LOW)
                    relaisstatus = "off"
                    logging.warning("Relais status changed manually: %s", relaisstatus)
        elif relais == "time":
            now = (datetime.now(timezone.utc))
            relaisontime = datetime.strptime(datetime.now().strftime("%Y-%m-%d-")+config['Relais']['RelaisOnTime']+" +0000",'%Y-%m-%d-%H:%M %z')
            relaisofftime = datetime.strptime(datetime.now().strftime("%Y-%m-%d-")+config['Relais']['RelaisOffTime']+" +0000",'%Y-%m-%d-%H:%M %z')
            relaisontimetomorrow = relaisontime + timedelta(days=1)
            relaisofftimeyesterday = relaisofftime + timedelta(days=-1)
            if GPIO.input(RelaisOn) == True:
                if relaisstatus != "on":
                    GPIO.output(Relais,GPIO.HIGH)
                    relaisstatus = "on"
                    logging.warning("Relais status changed manually: %s", relaisstatus)
            elif GPIO.input(RelaisOff) == True:
                if relaisstatus != "off":
                    GPIO.output(Relais,GPIO.LOW)
                    relaisstatus = "off"
                    logging.warning("Relais status changed manually: %s", relaisstatus)
            elif relaisontime < now < relaisofftime:
                if relaisstatus != "on":
                    GPIO.output(Relais,GPIO.HIGH)
                    relaisstatus = "on"
                    logging.warning("Relais status changed: %s", relaisstatus)
            elif relaisofftimeyesterday < now < relaisontime or relaisofftime < now < relaisontimetomorrow:
                if relaisstatus != "off":
                    GPIO.output(Relais,GPIO.LOW)
                    relaisstatus = "off"
                    logging.warning("Relais status changed: %s", relaisstatus)
        elif stop_threads:
            break

def main():
    t1 = threading.Thread(target=door)
    t1.start()
    t2 = threading.Thread(target=relais)
    t2.start()

if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(error.args[0])
    except KeyboardInterrupt:
        print("\nExiting application\n")
        # exit the applications
        stop_threads = True
        t1.join()
        t.join()
        GPIO.cleanup()
