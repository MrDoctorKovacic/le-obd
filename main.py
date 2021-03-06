"""
OBD - Python 2.7.13
Author: Quinn Casey
OBD logging to MySQL
"""

import obd
import MySQLdb
import time
import sys
import datetime
import logging

# Global OBD Connection
OBD_CONNECTION = None

def end_logging():
	""" Called to safely shutdown """
	logging.debug("Ending logging")
	sys.exit(0) # for now just die

def get_obd_value(command):
	try:
		result = OBD_CONNECTION.query(command).value 
		if result is None:
			return 0.1 
		else:
			return result.magnitude

	except Exception as e:
		# TODO: Better error handling, catch OBD exception
		logging.error("During get_obd_value the following exception occured:")
		logging.error(e)
		logging.error("Returning 0.1 and continuing...")
		return 0.1

def begin_logging(mysql_user, mysql_pass, mysql_db):

	# Break if the connection has dropped
	if not OBD_CONNECTION:
		return

	# TODO: Assume this will fail
	db = MySQLdb.connect("localhost", mysql_user, mysql_pass, mysql_db)
	curs = db.cursor()

	# init to 200 first, to get starting MAF and intake temp more frequently
	extra_i = 200
	while 1:
		# get RPMs
		rpm = get_obd_value(obd.commands.RPM)

		# get speed
		speed = get_obd_value(obd.commands.SPEED)

		# get engine load
		engine_load = get_obd_value(obd.commands.ENGINE_LOAD)

		# get MAF
		MAF = get_obd_value(obd.commands.MAF)

		write_db = True
		if(MAF == 0.1 and engine_load == 0.1 and speed == 0.1 and rpm == 0.1 or MAF == 0 and engine_load == 0 and speed == 0 and rpm == 0):
			write_db = False

		logging.debug("MAF: {}, ENGINE_LOAD: {}, SPEED: {}, RPM: {}".format(MAF, engine_load, speed, rpm))

		if(extra_i >= 200):
			# Get coolant and intake temp less frequently than the others
			extra_i = 0

			# get coolant temp
			coolant_temp = get_obd_value(obd.commands.COOLANT_TEMP)

			# get intake temp
			intake_temp = get_obd_value(obd.commands.INTAKE_TEMP)

			if write_db:
				with db:
					now = datetime.datetime.now()
					
					# With all that data, insert into MySQL
					curs.execute("""INSERT INTO log_obd
						(time, time_micro, speed, rpm, engine_load, coolant_temp, intake_temp, MAF)
						values (%s, %s, %s, %s, %s, %s, %s, %s)
						""", (str(now.strftime("%Y-%m-%d %H:%M:%S")), str(now.microsecond), str(speed), str(rpm), str(engine_load), str(coolant_temp), str(intake_temp), str(MAF)))
					db.commit()

		else:
			extra_i += 1
			if write_db:
				with db:
					now = datetime.datetime.now()

					# With all that data, insert into MySQL
					curs.execute("""INSERT INTO log_obd
						(time, time_micro, speed, rpm, engine_load, MAF)
						values (%s, %s, %s, %s, %s, %s)
						""", (str(now.strftime("%Y-%m-%d %H:%M:%S")), str(now.microsecond), str(speed), str(rpm), str(engine_load), str(MAF)))
					db.commit()

def setup_obd(waittime):
	if waittime >= 120:
		end_logging()

	# Wait to connect (for subsequent calls to this function)
	time.sleep(waittime)

	try:
		conn = obd.OBD("/dev/rfcomm0") # force connect to RF port
		return conn

	except:
		waittime += 15
		logging.debug("Failed to connect to OBD. Retrying in %d seconds." % waittime)
		setup_obd(waittime)

if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG)
	logging.debug("Starting OBD Connection...")

	if len(sys.argv) >= 4:
		OBD_CONNECTION = setup_obd(0)
		logging.debug("OBD Connection Successful")
		logging.debug("Starting OBD Logging...")
		begin_logging(sys.argv[1], sys.argv[2], sys.argv[3])

	else:
		print("Provide mysql username, password, and database")
