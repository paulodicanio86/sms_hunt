#!/usr/bin/python
import datetime as datetime
import os

import MySQLdb

from sms_hunt import db_config
from match_updates.get_daily_matches import (check_for_daily_file, get_matches_from_db,
                                             get_live_matches, compare_matches_and_update)

from IPython import embed

# Establish database connection
db = MySQLdb.connect(host=db_config['host'],
                     user=db_config['user'],
                     passwd=db_config['password'],
                     db=db_config['database'])

# Calculate current date and time
i = datetime.datetime.now()
date_str = str(i.strftime('%d.%m.%Y'))
time_str = str(i.strftime('%H:%M'))
hour_str = i.strftime('%H')
minute_str = i.strftime('%M')

# Set competition
competition = '1204'  # Premier League
minutes = ['0', '2', '4', '6', '8', '10', '12', '14', '16', '18',
           '20', '22', '24', '26', '28', '30', '32', '34', '36', '38',
           '40', '42', '44', '46', '48', '50', '52', '54', '56', '58']


# Check if daily file exists. if not create one. Retrieve trigger times.
# manually
file_path = 'match_updates/' + date_str + '.txt'
# automatically in cronjob
file_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(os.sep, file_path, 'match_updates', date_str + '.txt')

match_day, trigger_times = check_for_daily_file(db, file_path, date_str, competition)

# We have a match day today, and a valid hours and minute. Let's check the score
if match_day and (hour_str in trigger_times) and (minute_str in minutes):

    # Get matches in db
    db_matches = get_matches_from_db(db, date_str)
    if len(db_matches) > 0:
        print('no db matches found')
    # Get live matches
    live_matches = get_live_matches(date_str, competition='1204')
    if len(live_matches) > 0:
        print('no live matches found')

    # Compare both for score updates
    updated_matches = compare_matches_and_update(db, db_matches, live_matches)
    if len(updated_matches) > 0:
        print('matches with an update found!')
        # FIND PEOPLE SUBSCRIBED TO UPDATED MATCHES (localteamname + visitorteam_name)
        # AND SEND SMS
        embed()

    else:
        print('no update in any match')
        # do nothing



# Commit and close database connection
db.commit()
db.close()
