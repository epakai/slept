#!/usr/bin/python3
from pathlib import Path
import getpass
import os
import sqlite3
import argparse
import sys
from datetime import date, datetime
import time

def timespec_conversion(timespec):
    # ensure time contains one '-' and split it
    if (not '-' in timespec ):
        print('Bad time specification. "', timespec, '"', sep='', file=sys.stderr)
        sys.exit()
    times = timespec.split("-", 1)
    try:
        # create a tuple of start/end time
        sleeptime = (datetime.strptime(times[0], '%H:%M').time(), \
                datetime.strptime(times[1], '%H:%M').time())
    except ValueError:
        # strptime failed to parse the time
        print('Bad time specification. "', timespec, '"', sep="", file=sys.stderr)
        sys.exit()
    if (sleeptime[0] > sleeptime[1]):
        print('Bad time specification. Start time is after end time. "', \
                timespec, '"', sep="", file=sys.stderr)
        sys.exit()
    return sleeptime


def display_log():
    print("RUNNING DISPLAY LOG")
    return

try:
    config_file = Path( os.environ["XDG_CONFIG_HOME"] + "slept.conf" )
except KeyError:
    config_file = Path( "/home/" + getpass.getuser() + "/.config/slept.conf" )
config_file.parent.mkdir(0o700,parents=True,exist_ok=True)

try:
    db_file = Path( os.environ["XDG_DATA_HOME"] + "/slept/slept.db" )
except KeyError:
    db_file = Path( "/home/" + getpass.getuser() + "/.local/share/slept/slept.db" )
db_file.parent.mkdir(0o700,parents=True,exist_ok=True)
db_file.touch(mode=0o700,exist_ok=True)
conn = sqlite3.connect(str(db_file))

db = conn.cursor()

db.execute("CREATE TABLE IF NOT EXISTS sleep_times \
        (date TEXT, start_time TEXT, end_time TEXT)")
conn.commit()

parser = argparse.ArgumentParser(description='Slept - a sleep logger.')
parser.add_argument('-R', '--replace', dest='replace', action='store_true',
        help ='replace a previous date\'s entries')
# TODO -a add feature, but this feature would need to export current times for
# that date to ensure no overlap (move overlap check to a separate function)
parser.add_argument('-d', '--date', dest='date', type=str, nargs=1,
        help ='specify a prior date')
parser.add_argument('timespecs', type=str, nargs='*',
        help ='start and end time in 24-hour format separated by \'-\' ')
args = parser.parse_args()

if (not len(sys.argv) > 1):
    display_log()
    sys.exit()
if (not args.date == None):
    # convert date argument to a datetime object
    try:
        sleep_date = datetime.strptime(args.date[0], '%Y-%m-%d').date()
    except ValueError:
        try: 
            sleep_date = datetime.strptime(args.date[0], '%m-%d').date()
            sleep_date = sleep_date.replace(year=date.today().year)
        except ValueError:
            print('Invalid date argument. "', args.date[0], '"' \
                    , sep="", file=sys.stderr)
            sys.exit()
    if (sleep_date > date.today()):
        print('Cannot enter future sleep (check your date argument)', file=sys.stderr)
        sys.exit()
else:
    # use today's date if no argument
    sleep_date = date.today()

for row in db.execute("SELECT date FROM sleep_times WHERE date='" \
        + sleep_date.strftime("%Y-%m-%d") + "'"):
    if (args.replace):
        # delete all items with that date and continue
        db.execute("DELETE FROM sleep_times WHERE date='" \
                + sleep_date.strftime("%Y-%m-%d") + "'")
        print('replace')
    else:
        #date exists without --replace option given
        #TODO update this message if you add an addition feature
        print('Date "', args.date[0] \
                , '" already in database. Use \'-R\' to replace.' \
                , sep="", file=sys.stderr)
        sys.exit()
    break

sleep_times = sorted(list(map(timespec_conversion, args.timespecs)))
# check times don't overlap
for x,y in enumerate(sleep_times[:-1]):
    if (y[1] > sleep_times[x+1][0]):
        print('Times overlap. "', \
                y[0].strftime("%H:%M"), '-', y[1].strftime("%H:%M"), '"', \
                ' "', sleep_times[x+1][0].strftime("%H:%M"), \
                '-', sleep_times[x+1][1].strftime("%H:%M"), '"' \
                , sep="", file=sys.stderr)
        sys.exit()

for p in sleep_times:
    db.execute("INSERT INTO sleep_times VALUES ('" + sleep_date.strftime("%Y-%m-%d") \
            + "','" + p[0].strftime("%H:%M") + "','" + p[1].strftime("%H:%M") + "')")
    print('Added sleep time ' + p[0].strftime("%H:%M") + ' to ' \
            + p[1].strftime("%H:%M") + ' on ' + sleep_date.strftime("%Y-%m-%d"))
conn.commit()

    ################################ sample queries
#db.execute("INSERT INTO sleep_times VALUES
#        (date(''), time(''), time(''))")
#conn.commit()

#db.execute("SELECT * FROM sleep_times WHERE date = date('')")
#print(db.fetchall())

