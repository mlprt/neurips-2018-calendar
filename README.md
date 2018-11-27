# NeurIPS 2018 Calendar Generator
This script scrapes the event list from the NeurIPS website, and creates and populates calendars using the Google Calendar API. Pre-made calendars are also provided. The description for each event includes the list of authors, the abstract, and a link to details on the NeurIPS website.

This may be useful for those looking to customize their conference schedule or configure notifications for certain events. As some of the calendars have a number of overlapping events, switching to "Day" (rather than "Week") view results in a cleaner presentation.

Note that in the pre-made and public calendars:
- The event types "Talk", "Invited Talk", "Talk (Posner Lecture)", and "Talk (Breiman Lecture)" have been amalgamated into a single "Talk" calendar. 
- The "Poster" event type is excluded.
- A duplicate "Lunch on your own" event on Tuesday is removed.

## Pre-made calendar files
If you would like to be able to use or edit these calendars but do not want to run the script yourself, `.ics` files for each calendar/event type are provided [individually](https://github.com/mlprt/neurips-2018-calendar/blob/master/calendars.zip?raw=true), or as a single merged calendar [with](https://github.com/mlprt/neurips-2018-calendar/blob/master/calendars_merged.zip?raw=true) or [without](https://github.com/mlprt/neurips-2018-calendar/blob/master/calendars_merged_minimal.zip?raw=true) the "Spotlight" event type included. The files in these archives can be imported by Google Calendar, and probably by other calendar applications. (Note: If you want the calendars to remain separate after importing into Google Calendar, you may need to create empty calendars with appropriate names and selecting them in the import dialog.)

## Public calendars
If you only wish to view/subscribe to the calendars (but not edit them, I think) they are publicly available at the Google Calendar links provided [here](./public_links.md).

## Running the script yourself
1. Clone (or download and extract) this repository.
2. Enter the repository's working directory and run `pip install -r requirements.txt` (preferably within a new virtual environment).
3. Visit https://developers.google.com/calendar/quickstart/python to activate the Google Calendar API for your account, and place the resulting `credentials.json` file into the same directory as the script.
4. Edit the flags in `process_events.py` as desired (optional).
5. Run `python process_events.py`.

In order to minimize the number of requests to the NeurIPS website and Google Calendar API, and as the Poster events are so dense that the resulting calendar is basically useless, I suggest leaving `EXCLUDE_POSTERS = True`. If you intend to generate the same calendar multiple times (e.g. by switching out `credentials.json` for different accounts) then I suggest leaving `USE_SOURCE_BACKUP = True` as well, so that the website sources are only downloaded once; this also significantly speeds up subsequent runs. In this case, set `USE_HISTORY = False` (or delete `processed_event_ids.log` between generating each set of calendars) so that the script does not think it is repeating itself.
