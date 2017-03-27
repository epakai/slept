#!/usr/bin/python3
from pathlib import Path
import getpass
import os
import sqlite3
import argparse
import sys
from datetime import date, datetime

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

db.execute('''CREATE TABLE IF NOT EXISTS times
        (date TEXT, start_time TEXT, end_time TEXT)''')
conn.commit()

parser = argparse.ArgumentParser(description='Slept - a sleep logger.')
parser.add_argument('-a', '--amend', dest='amend', action='store_true',
        help ='amend a previous date\'s entry')
parser.add_argument('-d', '--date', dest='date', type=str, nargs=1,
        help ='specify a prior date')
parser.add_argument('timespec', type=str, nargs='*',
        help ='start and end time in 24-hour format separated by \'-\' ')
args = parser.parse_args()
print("### ARGS ###")
print(args.amend)
print(args.date)
print(args.timespec)
print("### ARGS ###")

if (not len(sys.argv) > 1):
    display_log()
    sys.exit()
if (not args.date == None):
    try:
        sleep_date = datetime.strptime(args.date[0], '%Y-%m-%d')
    except ValueError:
        try: 
            sleep_date = datetime.strptime(args.date[0], '%m-%d')
            sleep_date = sleep_date.replace(year=date.today().year)
        except ValueError:
            print('Invalid date argument')
            sys.exit()
    print(sleep_date)
# else
    # date is 'now'
# if date exists in db and -a not set
    # error mentioning -a option
# else if date exists and args.amend = True
    # delete all items with that date and continue
# check all time pairs for validity and non-overlapping (times are 24-hour


################################ sample queries
#db.execute('''INSERT INTO times VALUES
#        (date(''), time(''), time(''))''')
#conn.commit()

#db.execute('''SELECT * FROM times WHERE date = date('')''')
#print(db.fetchall())

