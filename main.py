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

def end_logging():
    """ Called to safely shutdown """
    print "Ending logging"
    sys.exit(0) # for now just die

def get_obd_value(command):
    try:
        result = connection.query(command).value 
        if result is None:
            return 0.1 
        else:
            return result.magnitude

    except Exception as e:
        # TODO: Better error handling
        print "[ERROR] During get_obd_value the following exception occured:"
        print e.message
        print "[ERROR] Returning 0.1 and continuing..."
        return 0.1

def begin_logging():

    # TODO: Assume this will fail
    db = MySQLdb.connect("localhost", "ellie", "ellie4815162342", "LE")
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

        if(extra_i >= 200):
            # Get coolant and intake temp less frequently than the others
            extra_i = 0

            # get coolant temp
            coolant_temp = get_obd_value(obd.commands.COOLANT_TEMP)

            # get intake temp
            intake_temp = get_obd_value(obd.commands.INTAKE_TEMP)

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
        conn = obd.OBD() # auto-connects to USB or RF port
        return conn

    except:
        waittime += 15
        print "Failed to connect to OBD. Retrying in %d seconds." % waittime
        setup_obd(waittime)

if __name__ == "__main__":
    print "Starting OBD Connection..."
    connection = setup_obd(0)
    print "OBD Connection Successful"

    print "Starting OBD Logging..."
    begin_logging()
