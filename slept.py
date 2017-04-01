#!/usr/bin/python3
from pathlib import Path
import getpass
import os
import sqlite3
import argparse
import sys
import datetime
import curses
import math

# array of times to be highlighted
ideal_time = [(datetime.time(22, 0), datetime.time(6, 0))]


def datespec_conv(datespec):
    # convert date argument to a datetime object
    try:
        sleep_date = datetime.datetime.strptime(datespec[0], '%Y-%m-%d').date()
    except ValueError:
        try:
            sleep_date = datetime.datetime.strptime(datespec[0], '%m-%d').date()
            sleep_date = sleep_date.replace(year=date.today().year)
        except ValueError:
            print('Invalid date argument. "', datespec[0], '"',
                  sep="", file=sys.stderr)
            sys.exit()

    if (sleep_date > datetime.date.today()):
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
        start = datetime.datetime.strptime(times[0], '%H:%M').time()
    except ValueError:
        try:
            start = datetime.datetime.strptime(times[0], '%H').time()
        except ValueError:
            print('Bad time specification. "', timespec,
                  '"', sep="", file=sys.stderr)
            sys.exit()

    try:
        end = datetime.datetime.strptime(times[1], '%H:%M').time()
    except ValueError:
        try:
            end = datetime.datetime.strptime(times[1], '%H').time()
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
        sleep_list.append((datetime.datetime.strptime(row[0], '%H:%M').time(),
                           datetime.datetime.strptime(row[1], '%H:%M').time()))

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


def sum_times(date):
    times = get_date_times(date)
    hours = 0
    minutes = 0
    for time in times:
        if (time[0].hour >= 12):
            if(time[1].hour < 12):
                hour = (time[1].hour + 12) - (time[0].hour - 12)
            else:
                hour = time[1].hour - time[0].hour

        else:
            if(time[1].hour < 12):
                hour = time[1].hour - time[0].hour
            else:
                hour = (time[1].hour - 12) - (time[0].hour + 12)

        if (time[0].minute > time[1].minute):
            hour = hour - 1
            minute = 60 - (time[0].minute - time[1].minute)
        elif (time[0].minute < time[1].minute):
            minute = time[1].minute - time[0].minute
        else:
            minute = 0

        hours = hours + hour
        minutes = minutes + minute

    if (minutes > 60):
        hours = hours + minutes // 60
        minutes = minutes % 60

    if (minutes > 30):
        return (hours + 1)
    else:
        return hours


def time_is_in_set(time, sleep_times):
    for sleeptime in sleep_times:
        if (sleep_time_key((time, None)) >= sleep_time_key(sleeptime) and
            sleep_time_key((time, None)) <= sleep_time_key((sleeptime[1], None))):
            return True

    return False


def scale_times(date, width):
    global ideal_time
    sleep_times = get_date_times(date)
    scale = 24/width
    first_half = []
    for block in range(math.floor(width/2), width):
        fraction_time = block * scale
        hours = math.floor(fraction_time)
        minutes = math.floor((fraction_time - hours) * 60)
        block_time = datetime.time(hours, minutes)
        if(time_is_in_set(block_time, sleep_times)):
            if (time_is_in_set(block_time, ideal_time)):
                first_half.append('#')
            else:
                first_half.append('%')

        else:
            first_half.append(' ')

    second_half = []
    for block in range(0, math.floor(width/2)):
        fraction_time = block * scale
        hours = math.floor(fraction_time)
        minutes = math.floor((fraction_time - hours) * 60)
        block_time = datetime.time(hours, minutes)
        if(time_is_in_set(block_time, sleep_times)):
            if (time_is_in_set(block_time, ideal_time)):
                second_half.append('#')
            else:
                second_half.append('%')

        else:
            second_half.append(' ')

    final = "".join(first_half) + "".join(second_half)
    return final


def draw_line(pos, date, win):
    # Date column
    height, width = win.getmaxyx()
    win.attrset(curses.color_pair(4))
    win.addstr(pos-1, 0, date.strftime('%Y-%m-%d'))
    win.attrset(curses.color_pair(1))
    win.vline(pos-1, 10, curses.ACS_VLINE, 1)

    # Time column
    times_chart = scale_times(date, width-11-13)
    times_chart_list = list(times_chart)
    for i in range(0, len(times_chart)):
        if (times_chart_list[i] is '%'):
            win.attrset(curses.color_pair(3))
            win.addch(pos-1, 11+i, curses.ACS_BLOCK)
        elif (times_chart_list[i] is '#'):
            win.attrset(curses.color_pair(7))
            win.addch(pos-1, 11+i, curses.ACS_BLOCK)
        else:
            win.addch(pos-1, 11+i, ' ')
    win.attrset(curses.color_pair(1))

    # Sum column
    win.vline(pos-1, width-13, curses.ACS_VLINE, 1)
    sleep_total = sum_times(date)
    for i in range(0, sleep_total):
        if (sleep_total <= 4):
            win.attrset(curses.color_pair(4))
        elif (sleep_total <= 6):
            win.attrset(curses.color_pair(5))
        else:
            win.attrset(curses.color_pair(2))
        win.addch(pos-1, width-12+i, curses.ACS_DIAMOND)
        win.attrset(curses.color_pair(1))
    for i in range(sleep_total, 12-sleep_total):
        win.addch(pos-1, width-12+i, ' ')
    win.refresh()
    return


def scroll_up(win, last_date):
    win.scroll(-1)
    height = win.getmaxyx()[0]-1
    new_date = last_date - datetime.timedelta(days=height)
    draw_line(1, new_date, win)
    return last_date - datetime.timedelta(days=1)


def scroll_down(win, last_date):
    if (last_date == datetime.date.today()):
        return last_date
    else:
        win.scroll(1)
        height = win.getmaxyx()[0]-1
        new_date = last_date + datetime.timedelta(days=1)
        draw_line(height, new_date, win)
        return new_date


def page_up(win, last_date):
    win.scroll(-win.getmaxyx()[0])
    height = win.getmaxyx()[0]-1
    last_date = last_date - datetime.timedelta(days=height)
    draw_screen(win, last_date)
    return last_date


def page_down(win, last_date):
    win.scroll(win.getmaxyx()[0])
    height = win.getmaxyx()[0]-1
    last_date = last_date + datetime.timedelta(days=height)
    if (last_date >= datetime.date.today()):
        last_date = datetime.date.today()

    draw_screen(win, last_date)
    return last_date


def draw_screen(win, last_date):
    height = win.getmaxyx()[0]-1
    for pos in range(height, 0, -1):
        draw_line(pos, last_date - datetime.timedelta(days=height-pos), win)
    return last_date


def input_function(key):
    keyaction = {
        ord('k'):         scroll_up,
        curses.KEY_UP:    scroll_up,
        ord('j'):         scroll_down,
        curses.KEY_DOWN:  scroll_down,
        curses.KEY_PPAGE: page_up,
        curses.KEY_NPAGE: page_down,
        curses.KEY_RESIZE: draw_screen,
    }
    return keyaction.get(key)


def draw_title(screen):
    screen.attrset(curses.color_pair(6))
    screen.addstr(0, 0, "   Date   ")
    screen.addch(0, 10, curses.ACS_VLINE)
    width = screen.getmaxyx()[1]
    mid_section_width = width - 11 - 13
    screen.addstr(0, 11, " "*mid_section_width)
    screen.addstr(0, 11 + math.floor(mid_section_width/4-3), "18:00")
    screen.addstr(0, 11 + math.floor(mid_section_width/2-4), "midnight")
    screen.addstr(0, 11 + math.floor(mid_section_width*(3/4)-3), "06:00")

    screen.addch(0, width-13, curses.ACS_VLINE)
    screen.addstr(0, width-12, "     Sum    ")
    screen.attrset(curses.color_pair(1))
    screen.refresh()


def display_log():
    os.environ.setdefault('ESCDELAY', '25')
    screen = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    try:
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, 0)
        curses.init_pair(2, curses.COLOR_GREEN, 0)
        curses.init_pair(3, curses.COLOR_CYAN, 0)
        curses.init_pair(4, curses.COLOR_RED, 0)
        curses.init_pair(5, curses.COLOR_YELLOW, 0)
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(7, curses.COLOR_BLUE, 0)
        draw_title(screen)
        win = curses.newwin(screen.getmaxyx()[0], screen.getmaxyx()[1], 1, 0)
        win.keypad(1)
        win.scrollok(1)
        last_date = datetime.date.today()
        draw_screen(win, last_date)

        key = win.getch()
        while (chr(key) is not 'q' and key is not 27):
            try:
                last_date = input_function(key)(win, last_date)
                if (key == curses.KEY_RESIZE):
                    draw_title(screen)
            except TypeError:
                pass
            key = win.getch()

    finally:
        screen.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
    return


def db_setup():
    'creates database, and table'
    try:
        db_file = Path(os.environ["XDG_DATA_HOME"] + "/slept/slept.db")
    except KeyError:
        db_file = Path("/home/" + getpass.getuser() +
                       "/.local/share/slept/slept.db")

    try:
        db_file.parent.mkdir(0o700, parents=True)
    except FileExistsError:
        pass

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
        sleep_date = datetime.date.today()

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
