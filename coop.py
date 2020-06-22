"""
Coop
A simple yet complete program to manage and monitor your coop.
Configuration is done in the config.ini file.
Logging is done to the file specified in this config.ini file
"""

#TODO: Make 'door' run at every whole minute with something like 'if secondold is > second then do this ... secondold = second'.
#TODO: Make 'door' the main script
#TODO: Implement early-open time
#TODO: Place variables in 'door' and 'startup', now they'll never change after initial startup
#TODO: Enable debug logging for the LED's
#TODO: Put motor in one definition with variables
#TODO: Put status(led) in one definition with variables

import logging
import configparser
from datetime import datetime, timezone, timedelta
import RPi.GPIO as GPIO
import time
from suntime import Sun
import threading
from astral import LocationInfo
from astral.sun import sun

# config
config = configparser.ConfigParser()
config.read('/home/pi/coop/coop.ini')

# logging
logging.basicConfig(filename=config['Settings']['LogFile'], level=config['Settings']['LogLevel'],
                    format='%(asctime)s - %(levelname)s: %(message)s')

# Suntime
city = LocationInfo("Wageningen", "Netherlands", "Europe/Amsterdam", float(config['Location']['Latitude']), float(config['Location']['Longitude']))
s = sun(city.observer, date=datetime.now(timezone.utc))
sun = Sun(float(config['Location']['Latitude']), float(config['Location']['Longitude']))
now = (datetime.now(timezone.utc))
offset = int(config['Door']['Offset'])
doortime_open: int = int(config['Door']['Doortime_Open'])
doortime_close: int = int(config['Door']['Doortime_Close'])
opentime = s["dawn"]
closetime = s["dusk"]
opentimetomorrow = sun.get_local_sunrise_time(datetime.now() + timedelta(days=1))
closetimeyesterday = sun.get_local_sunset_time(datetime.now() + timedelta(days=-1)) + timedelta(minutes=offset)
global stop_threads

# GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
TopSensor = int(config['GPIO']['TopSensor'])
BottomSensor = int(config['GPIO']['BottomSensor'])
GPIO.setup(TopSensor, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BottomSensor, GPIO.IN, pull_up_down=GPIO.PUD_UP)
MotorUp = int(config['GPIO']['IN3'])
GPIO.setup(MotorUp, GPIO.OUT)
MotorDown = int(config['GPIO']['IN4'])
GPIO.setup(MotorDown, GPIO.OUT)
StatusGreen = int(config['GPIO']['StatusGreen'])
GPIO.setup(StatusGreen, GPIO.OUT)
StatusRed = int(config['GPIO']['StatusRed'])
GPIO.setup(StatusRed, GPIO.OUT)
Led1 = int(config['GPIO']['Led1'])
GPIO.setup(Led1, GPIO.OUT)
Led2 = int(config['GPIO']['Led2'])
GPIO.setup(Led2, GPIO.OUT)
Led3 = int(config['GPIO']['Led3'])
GPIO.setup(Led3, GPIO.OUT)
PWM = int(config['GPIO']['ENb'])
GPIO.setup(PWM, GPIO.OUT)
p = GPIO.PWM(PWM, 100)
p.start(50)


def status_error():
    GPIO.output(StatusGreen, GPIO.LOW)
    GPIO.output(StatusRed, GPIO.HIGH)


def status_busy():
    while True:
        GPIO.output(StatusRed, GPIO.LOW)
        GPIO.output(StatusGreen, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(StatusGreen, GPIO.LOW)
        time.sleep(0.5)
        if stop_threads:
            break


def status_ok():
    GPIO.output(StatusGreen, GPIO.HIGH)
    GPIO.output(StatusRed, GPIO.LOW)


def lights(n):
    logging.debug("%s lights turned on",n)
    if n == 3:
        GPIO.output(Led1, GPIO.HIGH)
        GPIO.output(Led2, GPIO.HIGH)
        GPIO.output(Led3, GPIO.HIGH)
    elif n == 2:
        GPIO.output(Led1, GPIO.HIGH)
        GPIO.output(Led2, GPIO.LOW)
        GPIO.output(Led3, GPIO.HIGH)
    elif n == 1:
        GPIO.output(Led1, GPIO.LOW)
        GPIO.output(Led2, GPIO.HIGH)
        GPIO.output(Led3, GPIO.LOW)
    elif n == 0:
        GPIO.output(Led1, GPIO.LOW)
        GPIO.output(Led2, GPIO.LOW)
        GPIO.output(Led3, GPIO.LOW)


def open_door():
    global stop_threads
    stop_threads = False
    print("Open_Door")
    starttime = (datetime.now())
    t1 = threading.Thread(target=status_busy)
    t1.start()
    while True:
        motor_up()
        if GPIO.input(TopSensor) == False:
            motor_stop()
            logging.info("Door is open")
            stop_threads = True
            t1.join()
#            main_loop()
            break
        elif datetime.now() > starttime + timedelta(milliseconds=doortime_open):
            motor_stop()
            logging.error("ERROR, opening door took too long")
            stop_threads = True
            t1.join()
            status_error()
#            main_loop()
            break


def close_door():
    global stop_threads
    stop_threads = False
    print("Close_Door")
    starttime = (datetime.now())
    t1 = threading.Thread(target=status_busy)
    t1.start()
    while True:
        motor_down()
        if GPIO.input(BottomSensor) == False:
            time.sleep(4) #The sensor is a bit too sensitive (or not well enough placed) so to close entirely it needs another second
            motor_stop()
            logging.info("Door is closed")
            stop_threads = True
            t1.join()
#            main_loop()
            break
        elif datetime.now() > starttime + timedelta(milliseconds=doortime_close):
            motor_stop()
            logging.error("ERROR, closing door took too long")
            stop_threads = True
            t1.join()
            status_error()
#            main_loop()
            break


def motor_up():
    p.ChangeDutyCycle(75)
    GPIO.output(MotorUp, GPIO.HIGH)
    GPIO.output(MotorDown, GPIO.LOW)


def motor_down():
    p.ChangeDutyCycle(25)
    GPIO.output(MotorDown, GPIO.HIGH)
    GPIO.output(MotorUp, GPIO.LOW)


def motor_stop():
    GPIO.output(MotorUp, GPIO.LOW)
    GPIO.output(MotorDown, GPIO.LOW)


def startup():
    logging.info('Coop started')
    logging.info("The UTC time is: %s", now)
    if GPIO.input(TopSensor) == False and (closetimeyesterday < now < opentime or closetime < now < opentimetomorrow):
#        close_door()
        logging.warning("Door was open at startup while it should have been closed")
        lights(0)
        main_loop()
    elif opentime < now < closetime and GPIO.input(BottomSensor) == False:
#        open_door()
        logging.debug("Door was closed at startup while it should have been open")
        lights(3)
        main_loop()
    elif opentime < now < closetime and GPIO.input(TopSensor) == False:
        logging.info("Door was already open, lights turned on.")
        lights(3)
        main_loop()
    elif opentime < now < closetime:
#        open_door()
        logging.debug("Doorstatus could not be determined but door should have been and is now open.")
        lights(3)
        main_loop()
    elif GPIO.input(BottomSensor) == False  and (closetimeyesterday < now < opentime or closetime < now < opentimetomorrow):
        logging.info("Door was already closed, lights turned off..")
        lights(0)
        main_loop()
    elif (closetimeyesterday < now < opentime or closetime < now < opentimetomorrow):
#        close_door()
        logging.warning("Doorstatus could not be determined but door should have been and is now closed.")
        lights(0)
        main_loop()
#    elif GPIO.input(BottomSensor) and GPIO.input(TopSensor):
#        status_error()
#        logging.error('Door is stuck somewhere')


def door():
    opentime = sun.get_sunrise_time()
    closetime = sun.get_sunset_time() + timedelta(minutes=offset)
    opentimetomorrow = sun.get_local_sunrise_time(datetime.now() + timedelta(days=1))
    closetimeyesterday = sun.get_local_sunset_time(datetime.now() + timedelta(days=-1)) + timedelta(minutes=offset)
    now = (datetime.now(timezone.utc))
    next_open = opentime if opentime > now else opentimetomorrow
    next_close = closetime if closetime > now else (sun.get_local_sunset_time(datetime.now() + timedelta(days=1)) + timedelta(minutes=offset))
#    logging.debug("Door will open between %s and %s UTC", next_open,
#                  (next_open + timedelta(minutes=1)))
#    logging.debug("Door will close %s minutes after sunset between %s and %s UTC", offset,
#                  next_close, next_close + timedelta(minutes=1))
    if opentime <= now <= opentime + timedelta(minutes=1):
        logging.warning("Opening door")
        lights(3)
#        open_door()
        time.sleep(60)
#TODO: Fix this, this should prevent the open_door() to run multiple times which in turn should prevent the motor burning for lack of a topsensor.
        logging.debug("Door will open again at %s UTC", next_open)
        logging.debug("Door will close %s minutes after sunset at %s UTC", offset, next_close)
        main_loop()
    elif closetime <= now <= closetime + timedelta(minutes=1):
        logging.warning("Closing door")
        lights(0)
#        close_door()
        time.sleep(60)
        logging.debug("Door will open at %s UTC", next_open) 
        logging.debug("Door will close again %s minutes after sunset at %s UTC", offset, next_close)
        main_loop()
    elif GPIO.input(BottomSensor) == False and (closetimeyesterday < now < opentime or closetime < now < opentimetomorrow):
        status_ok()
        logging.debug("DoorClosedCheck: OK")
    elif opentime < now < closetime and GPIO.input(TopSensor) == False:
        status_ok()
        logging.debug("DoorOpenCheck: OK")
#        else:
#            status_error()
#            logging.error("DoorCheck: ERROR")


def main_loop():
    while True:
        door()
        time.sleep(60)


if __name__ == "__main__":
    try:
        startup()
    except RuntimeError as error:
        print(error.args[0])
    except KeyboardInterrupt:
        print("\nExiting application\n")
        # exit the applications
        GPIO.cleanup()
