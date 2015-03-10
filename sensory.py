#!/usr/bin/python

# sensory.py
#
# Script to fetch events from sensors via TellStick Duo (daemon /usr/sbin/telldusd).
#
# Push data to Twitter as @(my-account)
# Example:
#	Event @ 25.02.2015 00:46:49.
#	- Uptime: 101 days, 5:05:13.520000.
#	- Out: 22.1 (Degree char)C, In: 23.0 (Degree char)C / 25 % (RH).
#
# Jani Karhunen 28.2.2015

import getopt
import os
import sys
import td
import time
import twitter
from datetime import timedelta

# Global variables to hold the sensor values
globTemperatureOut = ""
globTemperatureLivingroom = ""
globHumidityLivingroom = ""

def logSensorEvent(protocol, model, id, dataType, value, timestamp, callbackId):
    global globTemperatureOut
    global globTemperatureLivingroom
    global globHumidityLivingroom

    # id 101 = temp. outdoors (Settings: House 10, Channel 1)
    # id 117 = Oregon, temp./RH indoors (Settings: Channel 2)

    if (id == 101 and dataType == 1):
        globTemperatureOut = value
    elif (id == 117 and dataType == 1):
        globTemperatureLivingroom = value
    elif (id == 117 and dataType == 2):
        globHumidityLivingroom = value

    return


def PrintUsageAndExit():
    print USAGE
    sys.exit(2)

def main():

	mycounter = 0
	global globTemperatureOut
	global globTemperatureLivingroom
	global globHumidityLivingroom


	try:
		shortflags = 'h'
		longflags = ['help', 'consumer-key=', 'consumer-secret=','access-key=', 'access-secret=', 'encoding=']
		opts, args = getopt.gnu_getopt(sys.argv[1:], shortflags, longflags)
	except getopt.GetoptError:
		PrintUsageAndExit()

	message = ' '.join(args)

	# Get the current system date and time

	nowdate = time.strftime("%d.%m.%Y")
	nowtime = time.strftime("%H:%M:%S")

	# Message does not necessarily have a value (e.g. when run from cron).
	if message:
		message = message + "\n\nTime now is " + nowdate + " " + nowtime + "."
	else:
		message = "Event @ " + nowdate + " " + nowtime + "."


	# System uptime (on Linux)

	if os.path.isfile('/proc/uptime'):
		with open('/proc/uptime', 'r') as f:
			uptime_seconds = float(f.readline().split()[0])
			uptime_string = str(timedelta(seconds = uptime_seconds))
			message = message + "\n- Uptime: " + uptime_string + "."


	# Sensor data
	# Sensors send the data once in every 60 sec. This is why quite a long delay and loop are needed.

	# Intialize the communcation
	td.init( defaultMethods = td.TELLSTICK_TURNON | td.TELLSTICK_TURNOFF )
    # Register callbacks
	callbackId = []
	callbackId.append(td.registerSensorEvent(logSensorEvent))
    # Run infinite loop
	try:
		while(mycounter < 1):
			time.sleep(61)
			mycounter = mycounter + 1
	except KeyboardInterrupt:
		for i in callbackId:
            # De-register callbacks
			td.unregisterCallback(i)
	finally:
		for i in callbackId:
            # De-register callbacks
			td.unregisterCallback(i)
    # Close communication so telldus-core can do some cleanup.
	td.close()


	# Append the data to message

	message = message + "\n- Out: " + str(globTemperatureOut) + " " + u"\u00B0" + "C, In: " + str(globTemperatureLivingroom) + " " + u"\u00B0" + "C / " + str(globHumidityLivingroom) + " % (RH)."


    # Push to Twitter

	api = twitter.Api(consumer_key='your-consumer-key',
		consumer_secret='your-consumer-secret',
	    access_token_key='your-access-token-key',
	    access_token_secret='your-access-token-secret')

	try:
		status = api.PostUpdate(message)

	except UnicodeDecodeError:
		print "Your message could not be encoded. Perhaps it contains non-ASCII characters?"
		sys.exit(2)

	#print message (for manual run)

	print "%s just posted: %s" % (status.user.name, status.text)

if __name__ == "__main__":
	main()
