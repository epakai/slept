#!/usr/bin/python3
import sqlite3
import getpass
import os
from pathlib import Path

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

db.execute('''INSERT INTO times VALUES
        (date('now'), time('12:30'), time('04:00'))''')
db.execute('''INSERT INTO times VALUES
        (date('now'), time('05:00'), time('07:00'))''')
conn.commit()

db.execute('''SELECT * FROM times WHERE date = date('now')''')
print(db.fetchall())
