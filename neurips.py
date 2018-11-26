import datetime
import re

import bs4
from dateutil.parser import parse
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from httplib2 import Http
from oauth2client import file, client, tools
import pytz
import requests

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar'

# URLs for the schedule and proceedings
SCHEDULE_URL = 'https://nips.cc/Conferences/2018/Schedule'
EVENT_URL_FMT = 'https://nips.cc/Conferences/2018/Schedule?showEvent={}'
PROC_URL = 'https://papers.nips.cc/book/advances-in-neural-information-processing-systems-31-2018'
PAPER_URL_FMT = 'https://papers.nips.cc{}'

# EVENT_TYPES = ['Tutorial', 'Break', 'Poster', 'Oral', 'Spotlight',
#                'Demonstration', 'Invited Talk', 'Workshop', 'Talk']

TIMEZONE = 'America/Montreal'  # this is an alias for America/Toronto
LOCATION = '1001 Jean Paul Riopelle Pl, Montreal, QC H2Z 1H5'

def main():
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))

    # get links to all papers
    proc_html = requests.get(PROC_URL).text
    proc_soup = bs4.BeautifulSoup(proc_html, 'html.parser')
    proc_tags = proc_soup.find_all(href=re.compile('/paper/'))
    papers = dict()
    for tag in proc_tags:
        paper_url = PAPER_URL_FMT.format(tag.attrs['href'])
        papers[tag.text] = paper_url

    # get all events (as HTML div tags)
    sched_html = requests.get(SCHEDULE_URL).text
    sched_soup = bs4.BeautifulSoup(sched_html, 'html.parser')
    event_divs = sched_soup.find_all(id=re.compile('maincard_'))

    # timezone object for formatting timestamps
    timezone = pytz.timezone(TIMEZONE)

    calendars = service.calendarList().list().execute()['items']
    calendar_ids = {c['summary']: c['id'] for c in calendars}

    for div in event_divs:
        # extract information from tags
        event_id = div.attrs['id'].split('_')[1]
        event_type = div.find(class_="pull-right maincardHeader maincardType").text
        event_sched = div.find(lambda tag: tag.get('class') == ["maincardHeader"]).text
        event_name = div.find(class_="maincardBody").text
        event_speakers = div.find(class_="maincardFooter").text.split('·')
        event_speakers = [s.strip() for s in event_speakers]

        if not event_type in calendar_ids:
            calendar = dict(
                summary=event_type,
                timeZone=TIMEZONE,
                location=LOCATION,
            )
            service.calendars().insert(body=calendar).execute()
            calendars = service.calendarList().list().execute()['items']
            calendar_ids = {c['summary']: c['id'] for c in calendars}

        # process event time and location
        time, loc = event_sched.split('@')
        start_str, end_str = time.split('--')
        start_strs = start_str.strip().split(' ')
        end_strs = end_str.strip().split(' ')
        if len(start_strs) == 4:
            # AM/PM same for start and end; add to start string for parsing
            start_strs += [end_strs[-1]]
        end_strs = start_strs[:-2] + end_strs
        start_time = parse(' '.join(start_strs))
        start_time = timezone.localize(start_time).isoformat('T')
        end_time = parse(' '.join(end_strs))
        end_time = timezone.localize(end_time).isoformat('T')

        # get event description from details page
        event_url = EVENT_URL_FMT.format(event_id)
        event_doc = requests.get(event_url).text
        event_soup = bs4.BeautifulSoup(event_doc, 'html.parser')
        event_description = event_soup.find(class_='abstractContainer').text

        event_description = (', '.join(event_speakers) + '\n\n'
                             + event_description)

        try:
            link_url = papers[event_name]
            file_url = link_url + '.pdf'
        except KeyError:
            link_url = event_url
            file_url = ""

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
        g_event = service.events().insert(calendarId=calendar_ids[event_type],
                                          body=event_spec)
        g_event.execute()

if __name__ == '__main__':
    main()
