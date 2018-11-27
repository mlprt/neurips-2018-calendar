# NeurIPS 2018 Calendar Generator
This script scrapes the event list from the NeurIPS website, and creates and populates calendars using the Google Calendar API. Pre-made calendars are also provided.

## Pre-made calendar files
If you would like to be able to use or edit these calendars but do not want to run the script yourself, `.ics` files for each calendar/event type are provided. These can be imported by Google Calendar, and probably by other calendar applications as well.

## Public calendars
If you only wish to view/subscribe to the calendars (but not edit them, I think) they are publicly available at the following links:

Break: https://calendar.google.com/calendar/b/2?cid=Yjl2Y240ZmRjaGVmMWxybXIxZHU2dXBycW9AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ
Demonstration: https://calendar.google.com/calendar/b/2?cid=Y2U1bDdsNGhsYjZmYzVoZWFmdTFmYmFwb29AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ
Oral: https://calendar.google.com/calendar/b/2?cid=N2doYW00amFsb3Y4dm43dTQ5OW1uZXVuZmdAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ
Spotlight: https://calendar.google.com/calendar/b/2?cid=b3V2ZXF0czR2cHM5OTdzdDlyMHQ0ZWEzODBAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ
Talk: https://calendar.google.com/calendar/b/2?cid=cjRsZGV2a2w3dWozNHI0bnFxYWltN29jOWtAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ
Tutorial: https://calendar.google.com/calendar/b/2?cid=YnI5NHMxc21qa3VvaTd1aDNhcDc4YTJxa2dAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ
Workshop: https://calendar.google.com/calendar/b/2?cid=bHFidXNxMjAzdjZtbTliamhuNmVtOG5ydTBAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ

## Running the script yourself
1. Clone (or download and extract) this repository.
2. Enter the repository's working directory and run `pip install -r requirements.txt` (preferably within a new virtual environment).
3. Visit https://developers.google.com/calendar/quickstart/python to activate the Google Calendar API for your account, and place the resulting `credentials.json` file into the same directory as the script.
4. Edit the flags in `process_events.py` as desired (optional).
5. Run `python process_events.py`.

In order to minimize the number of requests to the NeurIPS website and Google Calendar API, and as the Poster events are so dense that the resulting calendar is basically useless, I suggest leaving `EXCLUDE_POSTERS = True`. If you intend to generate the same calendar multiple times (e.g. by switching out `credentials.json` for different accounts) then I suggest leaving `USE_SOURCE_BACKUP = True` as well, so that the website sources are only downloaded once; this also significantly speeds up subsequent runs.
