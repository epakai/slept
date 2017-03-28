#!/usr/bin/python3
from pathlib import Path
import getpass
import os
import sqlite3
import argparse
import sys
from datetime import date, datetime


def datespec_conv(datespec):
    # convert date argument to a datetime object
    try:
        sleep_date = datetime.strptime(datespec[0], '%Y-%m-%d').date()
    except ValueError:
        try:
            sleep_date = datetime.strptime(datespec[0], '%m-%d').date()
            sleep_date = sleep_date.replace(year=date.today().year)
        except ValueError:
            print('Invalid date argument. "', datespec[0], '"',
                  sep="", file=sys.stderr)
            sys.exit()

    if (sleep_date > date.today()):
        print('Cannot enter future sleep (check your date argument)',
              file=sys.stderr)
        sys.exit()

    return sleep_date


def timespec_conv(timespec):
    # ensure time contains one '-' and split it
    if ('-' not in timespec):
        print('Bad time specification. "', timespec,
              '"', sep='', file=sys.stderr)
        sys.exit()

    times = timespec.split("-", 1)
    try:
        start = datetime.strptime(times[0], '%H:%M').time()
    except ValueError:
        try:
            start = datetime.strptime(times[0], '%H').time()
        except ValueError:
            print('Bad time specification. "', timespec,
                  '"', sep="", file=sys.stderr)
            sys.exit()

    try:
        end = datetime.strptime(times[1], '%H:%M').time()
    except ValueError:
        try:
            end = datetime.strptime(times[1], '%H').time()
        except ValueError:
            print('Bad time specification. "', timespec,
                  '"', sep="", file=sys.stderr)
            sys.exit()

    sleeptime = (start, end)
    if (sleep_time_key(sleeptime) > sleep_time_key((sleeptime[1], None))):
        print('Bad time specification. Start time is after end time. "',
              timespec, '"', sep="", file=sys.stderr)
        sys.exit()

    return sleeptime


def sleep_time_key(sleeptime):
    if (sleeptime[0].hour >= 12):
        sort_key = (sleeptime[0].hour - 12) * 100
    else:
        sort_key = (sleeptime[0].hour + 12) * 100

    sort_key = sort_key + sleeptime[0].minute
    return sort_key


def check_times_overlap(sleep_times):
    for x, y in enumerate(sleep_times[:-1]):
        # Compare end time (y[1]) with start time of next
        if (sleep_time_key((y[1], None)) > sleep_time_key(sleep_times[x+1])):
            print('Times overlap. "',
                  y[0].strftime("%H:%M"), '-', y[1].strftime("%H:%M"), '"',
                  ' "', sleep_times[x+1][0].strftime("%H:%M"),
                  '-', sleep_times[x+1][1].strftime("%H:%M"), '"',
                  sep="", file=sys.stderr)
            sys.exit()

    return


def insert_times(sleep_times, sleep_date):
    for p in sleep_times:
        db.execute("INSERT INTO sleep_times VALUES ('" +
                   sleep_date.strftime("%Y-%m-%d") + "','" +
                   p[0].strftime("%H:%M") + "','" +
                   p[1].strftime("%H:%M") + "')")
        print('Added sleep time ' + p[0].strftime("%H:%M") + ' to ' +
              p[1].strftime("%H:%M") + ' on ' +
              sleep_date.strftime("%Y-%m-%d"))

    conn.commit()
    return


def get_date_times(date):
    sleep_list = []
    for row in db.execute("SELECT start_time, end_time " +
                          "FROM sleep_times WHERE date='"
                          + date.strftime("%Y-%m-%d") + "'"):
        sleep_list.append((datetime.strptime(row[0], '%H:%M').time(),
                           datetime.strptime(row[1], '%H:%M').time()))

    return sleep_list


def date_in_db(date):
    for row in db.execute("SELECT date FROM sleep_times WHERE date='" +
                          date.strftime("%Y-%m-%d") + "'"):
        return True


def delete_date_times(date):
    for row in db.execute("SELECT date, start_time, end_time " +
                          "FROM sleep_times WHERE date='"
                          + date.strftime("%Y-%m-%d") + "'"):
        print('Deleted sleep time ' + row[1] + ' to ' + row[2] +
              ' on ' + row[0])

    db.execute("DELETE FROM sleep_times WHERE date='" +
               date.strftime("%Y-%m-%d") + "'")
    conn.commit()
    return


def scale_times(date, width):
    return


def display_log():
    print("RUNNING DISPLAY LOG")
    return


def db_setup():
    'creates database, and table'
    try:
        db_file = Path(os.environ["XDG_DATA_HOME"] + "/slept/slept.db")
    except KeyError:
        db_file = Path("/home/" + getpass.getuser() +
                       "/.local/share/slept/slept.db")

    db_file.parent.mkdir(0o700, parents=True, exist_ok=True)
    db_file.touch(mode=0o700, exist_ok=True)
    global conn, db
    conn = sqlite3.connect(str(db_file))

    db = conn.cursor()

    db.execute("CREATE TABLE IF NOT EXISTS sleep_times" +
               "(date TEXT, start_time TEXT, end_time TEXT)")
    conn.commit()
    return


def argument_setup():
    parser = argparse.ArgumentParser(description='Slept - a sleep logger.')
    parser.add_argument('-R', '--replace', dest='replace', action='store_true',
                        help='replace a previous date\'s entries')
    parser.add_argument('--delete', dest='delete', action='store_true',
                        help='delete a date\'s entries')
    parser.add_argument('-a', '--add', dest='add', action='store_true',
                        help='add time(s) to a previous date\'s entries')
    parser.add_argument('-d', '--date', dest='date', type=str, nargs=1,
                        help='specify a prior date')
    parser.add_argument('timespecs', type=str, nargs='*',
                        help='start and end time in ' +
                             '24-hour time separated by \'-\' ')
    return parser.parse_args()


def main():
    db_setup()
    args = argument_setup()

    if (not len(sys.argv) > 1):
        display_log()
        sys.exit()

    if (args.date):
        sleep_date = datespec_conv(args.date)
    else:
        sleep_date = date.today()

    if (args.delete):
        delete_date_times(sleep_date)

    if (date_in_db(sleep_date)):
        if (args.replace):
            delete_date_times(sleep_date)
        elif (args.add):
            old_times = get_date_times(sleep_date)
            new_times = list(map(timespec_conv, args.timespecs))
            sleep_times = sorted(old_times + new_times, key=sleep_time_key)
            check_times_overlap(sleep_times)  # exits on overlap
            insert_times(new_times, sleep_date)
            conn.close()
            return
        else:
            # date exists without replace or add option given
            print('"', sleep_date.strftime('%Y-%m-%d'),
                  '" already in database. ',
                  'Use \'-R\' to replace, or \'-a\' to add new times.',
                  sep="", file=sys.stderr)
            sys.exit()

    # convert input to a list of sleeptime tuples
    sleep_times = sorted(list(map(timespec_conv, args.timespecs)),
                         key=sleep_time_key)
    check_times_overlap(sleep_times)
    insert_times(sleep_times, sleep_date)
    conn.close()
    return


if __name__ == "__main__":
    main()
