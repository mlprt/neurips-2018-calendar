import datetime
import re

import bs4
from dateutil.parser import parse
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import requests

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar'

# URL to the
SCHEDULE_URL = 'https://nips.cc/Conferences/2018/Schedule'

def main():
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))

    # function showDetail(eventID){
    # window.location.assign("/Conferences/2018/Schedule?showEvent=" + eventID);
    # }
    html_doc = requests.get(SCHEDULE_URL).text

    cards = dict()
    soup = bs4.BeautifulSoup(html_doc, 'html.parser')
    card_divs = soup.find_all(id=re.compile('maincard_'))

    for div in card_divs:
        card_id = div.attrs['id'].split('_')[1]
        card_type = div.find(class_="pull-right maincardHeader maincardType").text
        card_sched = div.find(lambda tag: tag.get('class') == ["maincardHeader"]).text
        card_name = div.find(class_="maincardBody").text
        card_speakers = div.find(class_="maincardFooter").text.split('·')
        card_speakers = [s.strip() for s in card_speakers]

        # process event time and location
        time, loc = card_sched.split('@')
        start_str, end_str = card_sched.split('--')
        start_strs = start_str.strip().split(' ')
        end_strs = end_str.strip().split(' ')
        if len(start_strs) == 4:
            # AM/PM same for start and end; add to start string for parsing
            start_strs += [end_strs[-1]]
        end_strs = start_strs[:-2] + end_strs
        start_time = parse(' '.join(start_strs))
        end_time = parse(' '.join(end_strs))


if __name__ == '__main__':
    main()
