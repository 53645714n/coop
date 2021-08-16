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
Install python modules
```
pip3 install -r requirements.txt
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

## Startup
To enable the program on startup, enter:
```
sudo mv coop.service /etc/systemd/system
sudo systemctl enable coop.service
```
