import schedule
import time
import RPi.GPIO as GPIO

def lights():
	red = 10
	green = 12
	GPIO.setmode(GPIO.BOARD)
#	GPIO.setwarnings(False)
	GPIO.setup(GREEN,GPIO.OUT)
	GPIO.setup(RED,GPIO.OUT)
#	print("Green LED for 10 seconds")
	GPIO.output(GREEN,GPIO.HIGH)
	GPIO.output(RED,GPIO.LOW)
	time.sleep(10)
#	print( "Red LED for 10 seconds")
	GPIO.output(GREEN,GPIO.LOW)
	GPIO.output(RED,GPIO.HIGH)
	time.sleep(10)
	GPIO.cleanup()

def schedule_task():
	schedule.every(30).seconds.do(lights)

while True:
    schedule.run_pending()
    time.sleep(1)
