import time
import sys
import datetime
import csv
import re

if __name__ == "__main__":
 
    with open('/Users/casey/Dropbox/log_obd.csv', 'rb') as f:
        reader = csv.reader(f)
        last_row = []
        total_time = datetime.timedelta(seconds=0)
        total_rpms = 0
        total_engine_load = 0
        total_high_rpms = 0
        total_speed = 0

        i = 0
        ri = 0
        rpm_i = 0
        el_i = 0
        rpm_high_i = 0
        speed_i = 0

        for row in reader:

            # Make sure we're not messing with any weird entries
            # 0-81 happened to be extra weird in this CSV
            if i > 81 and last_row is not None and row[1] is not "0000-00-00 00:00:00" and last_row[1] is not "0000-00-00 00:00:00":
                ri += 1

                # Get difference between last sample time and now
                row_delta = datetime.datetime.strptime(
                    row[1], "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(last_row[1], "%Y-%m-%d %H:%M:%S")

                # If there's a major difference in time (>60 seconds)
                #   assume we're dealing with a restart of the OBD script
                #   ignore and skip
                # Otherwise add to our running total
                if (row_delta < datetime.timedelta(seconds=60)):
                    total_time += row_delta

                    # Measure average normal RPMs 
                    if int(row[4]) > 0:
                        total_rpms += int(row[4])
                        rpm_i += 1

                    # Measure average engine load
                    if int(row[5]) > 0:
                        total_engine_load += int(row[5])
                        el_i += 1

                    # Measure average RPMs > 3500 (when I'm really getting on it)
                    if int(row[4]) > 3500:
                        total_high_rpms += int(row[4])
                        rpm_high_i += 1

                    # Measure average speed (HIGHLY inaccurate, since it counts my time idling at warmup)
                    total_speed += int(row[3])
                    speed_i += 1
                    
            last_row = row
            i += 1

        print "Total rows: {}\nTotal Time Recorded: {}\nAverage Sample Rate: {}".format(
                ri, total_time, total_time / ri)
        print "Average RPMs: {}\nAverage Speed: {}mph\nAverage Engine Load: {}\nAverage High RPM (>3500): {}".format(
                total_rpms / rpm_i, total_speed / speed_i, total_engine_load / el_i, total_high_rpms / rpm_high_i)
