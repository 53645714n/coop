'''
Coop

A simple yet complete porgram to manage and monitor your coop.

Configuration is done in the config.ini file.
Logging is done to the file specified in this config.ini file

'''

import logging
import configparser
from datetime import datetime, timezone, timedelta
import RPi.GPIO as GPIO
import time
from suntime import Sun, SunTimeException

#config
config = configparser.ConfigParser()
config.read('coop.ini')

#logging
logging.basicConfig(filename=config['Settings']['LogFile'], level=config['Settings']['LogLevel'], format='%(asctime)s - %(levelname)s: %(message)s')

#Suntime
sun = Sun(float(config['Location']['Latitude']), float(config['Location']['Longitude']))
#now = (datetime.now(timezone.utc) + timedelta( hours=7))
offset = int(config['Door']['Offset'])
doortime = int(config['Door']['Doortime'])

#GPIO
GPIO.setmode(GPIO.BOARD)
TopSensor= int(config['GPIO']['TopSensor'])
BottomSensor = int(config['GPIO']['BottomSensor'])
GPIO.setup(TopSensor, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BottomSensor, GPIO.IN, pull_up_down=GPIO.PUD_UP)
MotorUp = int(config['GPIO']['MotorUp'])
GPIO.setup(MotorUp,GPIO.OUT)
MotorDown = int(config['GPIO']['MotorDown'])
GPIO.setup(MotorDown,GPIO.OUT)
StatusGreen = int(config['GPIO']['StatusGreen'])
GPIO.setup(StatusGreen,GPIO.OUT)
StatusRed = int(config['GPIO']['StatusRed'])
GPIO.setup(StatusRed,GPIO.OUT)
Light = int(config['GPIO']['Light'])
GPIO.setup(Light,GPIO.OUT)

def status_error():
	GPIO.output(StatusGreen,GPIO.LOW)
	GPIO.output(StatusRed,GPIO.HIGH)

def status_busy():
	GPIO.output(StatusRed,GPIO.LOW)
	GPIO.output(StatusGreen,GPIO.HIGH)
	time.sleep(0.5)
	GPIO.output(StatusGreen,GPIO.LOW)
	time.sleep(0.5)

def status_ok():
	GPIO.output(StatusGreen,GPIO.HIGH)
	GPIO.output(StatusRed,GPIO.LOW)

def motor_up():
	GPIO.output(MotorUp,GPIO.HIGH)
	GPIO.output(MotorDown,GPIO.LOW)
	status_busy()

def motor_down():
	GPIO.output(MotorDown,GPIO.HIGH)
	GPIO.output(MotorUp,GPIO.LOW)
	status_busy()

def motor_stop():
	GPIO.output(MotorUp,GPIO.LOW)
	GPIO.output(MotorDown,GPIO.LOW)

def startup():
	logging.info('Coop started')
#	logging.info("The UTC time is: %s", (now))

def door():
	now = datetime.now(timezone.utc)
	closetime = sun.get_sunset_time() + timedelta(minutes=(offset))
	opentime = sun.get_sunrise_time()
	logging.debug("The UTC time is: %s", (now))
	logging.info("Door will open between %s and %s UTC",(sun.get_sunrise_time()), (sun.get_sunrise_time() + timedelta(minutes=2)))
	logging.info("Door will close %s minutes after sunset between %s and %s UTC", (offset), (sun.get_sunset_time() + timedelta(minutes=(offset))), (sun.get_sunset_time() + timedelta(minutes=(offset)) + timedelta(minutes=2)))
	count = 0
#	now = (datetime.now(timezone.utc) + timedelta( hours=7))
	if now >= sun.get_sunrise_time() and now <= sun.get_sunrise_time() + timedelta(minutes=2):
		logging.warning("It is day, opening door")
		GPIO.output(Light,GPIO.HIGH)
#		while GPIO.input(TopSensor) == False and count < doortime:
#			motor_up()
#			status_busy()
#			count = count + 1
#			logging.debug(count)
#			logging.debug("Door going up")
#			if GPIO.input(TopSensor) and GPIO.input(BottomSensor) == False:
#				motor_stop()
#				logging.info("Door is open")
#				status_ok()
#			if GPIO.input(TopSensor) == False and count == doortime:
#				motor_stop()
#				logging.error("ERROR, opening door took too long")
#				status_error()
	elif now >= sun.get_sunset_time() + timedelta(minutes=(offset)) and now <= sun.get_sunset_time() + timedelta(minutes=(offset)) +  timedelta(minutes=2):
		logging.warning("It is night, closing door")
		GPIO.output(Light,GPIO.LOW)
#		while GPIO.input(BottomSensor) == False and count < doortime:
#			motor_down()
#			status_busy()
#			count = count + 1
#			logging.debug(count)
#			logging.debug("Door going down")
#			if GPIO.input(BottomSensor) and GPIO.input(TopSensor) == False:
#				motor_stop()
#				logging.info("Door is closed")
#				status_ok()
#			if GPIO.input(BottomSensor) == False and count == doortime:
#				motor_stop()
#				logging.error("ERROR, closing door took too long")
#				status_error()
	elif GPIO.input(BottomSensor) and ( now < opentime or now > closetime ) :
		status_ok()
		logging.debug("DoorClosedCheck: OK")
	elif now > opentime and now < closetime and GPIO.input(TopSensor):
		status_ok()
		logging.debug("DoorOpenCheck: OK")
	else:
		status_error()
		logging.error("DoorCheck: ERROR")

def main_loop():
	while True:
		door()
		time.sleep(60)

if __name__ == "__main__":
	try:
		startup()
		main_loop()
	except RuntimeError as error:
		print(error.args[0])
	except KeyboardInterrupt:
		print("\nExiting application\n")
		# exit the applications
		GPIO.cleanup()
