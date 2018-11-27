"""Create Google calendar events from the NeurIPS 2018 website event list.

Scrapes event data from https://nips.cc using `requests` and BeautifulSoup.
Creates and populates a separate calendar for each event type. Metadata
includes the full description/abstract prepended with the author/speaker names,
as well as a link to the event details page (or the proceedings page, when
possible).

If the `USE_HISTORY` constant is `True`, the IDs of processed events will be
logged, and IDs encountered more than once will be skipped. In a single session
this should not happen (i.e. no repeat IDs in the entire list of events on the
website), but this allows the creation of the calendar to take place over
multiple sessions, if necessary.

If `USE_SOURCE_BACKUP` is `True`, the HTML strings pulled during previous
sessions will be used, if available. The most recently pulled HTML is stored
automatically in a JSON file. The intention is to (maybe) reduce the number of
requests to the NeurIPS website.

Before running, visit https://developers.google.com/calendar/quickstart/python
to activate the Google Calendar API, and place the `credentials.json` file in
the same directory as this script.

The Google Calendar API authentication code is derived from the guides linked
above.
"""

import json
import re

from bs4 import BeautifulSoup
from dateutil.parser import parse
from googleapiclient.discovery import build
#from googleapiclient.errors import HttpError
from httplib2 import Http
from oauth2client import file, client, tools
import pytz
import requests

# exclude posters from the calendar
# NOTE: much faster when `True` & poster calendar is basically unusable anyway
EXCLUDE_POSTERS = True
POSTER_EVENT_TYPE = 'Poster'

# if True, keep record of processed events, and don't repeat additions
USE_HISTORY = True
HISTORY_FILE = 'processed_event_ids.log'


# if True, use previously-scraped copy of website HTML (minimize traffic)
USE_SOURCE_BACKUP = True
SOURCE_BACKUP_FILE = 'source_backup.json'

# If you change this, delete token.json.
OAUTH_SCOPE = 'https://www.googleapis.com/auth/calendar'

# BeautifulSoup things
HTML_PARSER = 'html.parser'

# URLs of pages with data to be scraped
SCHEDULE_URL = 'https://nips.cc/Conferences/2018/Schedule'
EVENT_URL = 'https://nips.cc/Conferences/2018/Schedule?showEvent='
PAPERS_URL = 'https://papers.nips.cc'
PROC_URL = ('https://papers.nips.cc/book/'
            + 'advances-in-neural-information-processing-systems-31-2018')

# location
# see https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
TIMEZONE = 'America/Montreal'  # this is an alias for America/Toronto
LOCATION = '1001 Jean Paul Riopelle Pl, Montreal, QC H2Z 1H5'

# load
SOURCE_BACKUP = dict()

def load_json(json_path):
    """Try to load a JSON file, or return an empty dictionary."""
    try:
        with open(json_path, 'r') as jsonf:
            parsed = json.load(jsonf)
    except FileNotFoundError:
        parsed = dict()
    return parsed

def update_json(entry, json_path=SOURCE_BACKUP_FILE):
    """Add an entry to a JSON file."""
    parsed = load_json(json_path)
    parsed.update(entry)
    with open(json_path, 'w') as jsonf:
        json.dump(parsed, jsonf)
    return parsed

def find_all_url(url, source_backup=None, **kwargs):
    """Shorthand for BeautifulSoup `find_all` on a url, by `requests`.

    If `url` is a key in `source_backup`, the corresponding value is taken as
    the HTML string to be parsed.

    Automatically backs up scraped HTML to disk, to reduce number of requests.
    """
    if url in source_backup:
        html = source_backup[url]
    else:
        html = requests.get(url).text
        update_json({url: html})
    soup = BeautifulSoup(html, HTML_PARSER)
    found = soup.find_all(**kwargs)
    return found, html

def datetime_strs_to_rfc3339(strs, tz=timezone):
    """Parse list of partial datetime strings, output RFC 3339 timestamp.

    Some partial datetime strings are: "Mon", "Dec", "3" (or "3rd"),
    "12:00:00".
    """
    dt = parse(' '.join(strs))
    dt_loc = timezone.localize(dt)
    rfc = dt_loc.isoformat('T')
    return rfc

def main():
    # Google authentication
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', OAUTH_SCOPE)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))

    # load backup of website HTML if toggled
    source_backup = dict()
    if USE_SOURCE_BACKUP:
        source_backup = load_json(SOURCE_BACKUP_FILE)

    # get links to all papers
    proc_tags = find_all_url(PROC_URL, source_backup=source_backup,
                             href=re.compile('/paper/'))
    papers = dict()
    for tag in proc_tags:
        papers[tag.text] = PAPERS_URL + tag.attrs['href']

    # get all div tags corresponding to events
    event_tags = find_all_url(SCHEDULE_URL, url=source_backup=source_backup,
                              id=re.compile('maincard_'))

    # timezone object for localizing timestamps
    timezone = pytz.timezone(TIMEZONE)

    # get metadata for existing calendars on account
    calendars = service.calendarList().list().execute()['items']
    calendar_ids_by_name = {c['summary']: c['id'] for c in calendars}
    # make sure a calendar exists for each event type
    event_types = [d.find(class_="pull-right maincardHeader maincardType").text
                   for d in event_tags]
    new_calendar_names = [event_type in set(event_types)
                          if not event_type in calendar_ids_by_name]
    if any(new_calendar_names):
        calendar = dict(
            summary=event_type,
            timeZone=TIMEZONE,
            location=LOCATION,
        )
        service.calendars().insert(body=calendar).execute()

        # need the IDs generated for the new calendars
        calendars = service.calendarList().list().execute()['items']
        calendar_ids_by_name = {c['summary']: c['id'] for c in calendars}

    # try to load history if toggled
    if USE_HISTORY:
        try:
            with open(HISTORY_FILE, 'r') as history_file:
                processed_events = [int(line.rstrip())
                                    for line in history_file.readlines()]
        except FileNotFoundError:
            processed_events = []

    # process the list of events
    for div, event_type in zip(event_tags, event_types):
        event_id = int(div.attrs['id'].split('_')[1])
        if USE_HISTORY:
            if event_id in processed_events:
                continue

        if EXCLUDE_POSTERS:
            if re.search(POSTER_EVENT_TYPE, event_type):
                # it's a poster and we're skipping posters
                continue

        # extract information from tags
        event_name = div.find(class_="maincardBody").text
        event_sched = div.find(lambda tag: tag.get('class') == ["maincardHeader"]).text
        event_speakers = div.find(class_="maincardFooter").text.split('·')
        event_speakers = [s.strip() for s in event_speakers]

        if VERBOSE:
            print()

        # process event time and location
        time, loc = event_sched.split('@')
        start_str, end_str = time.split('--')
        start_strs = start_str.strip().split(' ')
        end_strs = end_str.strip().split(' ')
        if len(start_strs) == 4:
            # AM/PM same for start and end; add to start string for parsing
            start_strs += [end_strs[-1]]
        end_strs = start_strs[:-2] + end_strs
        start_time = datetime_strs_to_rfc3339(start_strs)
        end_time = datetime_strs_to_rfc3339(end_strs)

        # get event description from details page
        event_description = find_all_url(EVENT_URL + str(event_id),
                                         source_backup=source_backup,
                                         class_='abstractContainer')[0].text

        # add list of authors/speakers at the start of the description
        event_description = (', '.join(event_speakers) + '\n\n'
                             + event_description)

        # if the event title is in the proceedings, link to there. else details
        # NOTE: I'm not sure this does anything. I don't see any attachments.
        try:
            link_url = papers[event_name]
            file_url = link_url + '.pdf'
        except KeyError:
            link_url = event_url
            file_url = ""

        # information needed to add the event to the calendar
        event_spec = dict(
            summary=event_name,
            location=loc,
            description=event_description,
            start=dict(
                dateTime=start_time,
                timeZone=TIMEZONE,
            ),
            end=dict(
                dateTime=end_time,
                timeZone=TIMEZONE,
            ),
            source=dict(
                url=link_url,
            ),
            attachments=[dict(
                fileUrl= file_url,
            )]
        )

        # add to calendar
        calendar_id = calendar_ids_by_name[event_type]
        g_event = service.events().insert(calendarId=calendar_id,
                                          body=event_spec)
        g_event.execute()

        # keep track, if ordered
        if USE_HISTORY:
            processed_events.append(event_id)
            with open(HISTORY_FILE, 'a') as history_file:
                print(event_id, file=history_file)

if __name__ == '__main__':
    main()
