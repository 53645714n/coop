# coop

I created this program to automate my chicken coop by opening the door and turning on the light on the inside. Build instructions can be found in the wiki, together with more detailed instructions on how to setup.
## Configuration

### RTC
https://trick77.com/adding-ds3231-real-time-clock-raspberry-pi-3/

### Turn off all LED's
Add this to the bottom of /boot/config.txt
```
# Disable the ACT LED on the Pi Zero.
dtparam=act_led_trigger=none
dtparam=act_led_activelow=on
```

## Installation

Install git
```
sudo apt install git python3-pip
```
Install suntime module
```
pip3 install suntime
```

Clone the repository
```
git clone https://github.com/53645714n/coop.git
```

Then, go to the directory:

```
cd coop
```

## Configuration
Then, to edit the config file:

```
nano coop.ini
```

Edit at least your location, the rest *can* be the same. It can also be totally different, up to you. To save, type: ctrl + o, ctrl + m, ctrl + x.

## Startup and shutdown
To start the script, enter:

```
python3 coop.py &
```

To run persistent, after logging off or shutting down the remote pc:

```
nohup python3 coop.py &
```

and view the logging:

```
tail -f coop.log
```

To stop executing the script find the PID first

```
pidof python3 coop.py
```

and type the results after kill -9 like this

```
kill -9 PID
```
