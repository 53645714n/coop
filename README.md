## To Do:
- threads for lights, maybe add status open and status closed? (e.g. green blinking light is busy, red blinking light is error, red constant is closed, green constant is open?)
- add sunset times for yesterday and sunrise times for tomorrow in status definition in stead of dirty 'or'
- create script to deteremine door open and door close times. Maybe add buttons while on it?

# coop

I created this program to automate my chicken coop by opening the door and turning on the light on the inside. Build instructions can be found in the wiki, together with more detailed instructions on how to setup.

## Installation
Simply enter the following command in your terminal

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
To start the script, enter:

```
python3 coop.py &
```
and view the logging:

```
tail -f coop.log
```

To stop executing the script type:

```
kill -9 PROCESS
```

Where PROCESS is the number the terminal returned afther startup.

