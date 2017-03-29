## Synopsis

Slept is a command line sleep logger and log viewer.

It uses 24-hour times, and each date encompasses the 24 hours before noon that day.

It is written in python, uses curses for display, and sqllite to store entries.

![Slept display log output](/shot.png)

## Usage

Slept takes new entries from command line arguments.
It errors on these conditions:

* Date already in database (override with **-R** or **-a**)
* Future dates are not accepted
* Invalid times or out of order times (start after finish)
* Overlapping times


New entry:

	slept.py 15-5:30 6-8

New entry with date:

	slept.py -d 2-28 22-6

Replace entries (full date is optional, current year will be used):

	slept.py -R -d 2017-02-28 20-5

Add time to a date:

	slept.py -a -d 2-28 6:30-9

Delete today's entries (or combine with **-d** option):

	slept.py --delete

When called without arguments it displays sleep logs in console with 
each line representing a day's sleep.

The sleep log can be navigated with cursor keys, page up/down, or j/k.

## TODO
Slept should also be able to jump to a specific date in the log.

