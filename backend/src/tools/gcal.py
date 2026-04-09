import sys
import os
import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from auth import get_calendar_service

service = get_calendar_service()


def get_calendar_events():
    """
    Retrieves a list of upcoming events from the user's Google Calendar.
    Use this whenever the user asks about their schedule or free time.
    """
    now = datetime.datetime.utcnow().isoformat() + 'Z' 
    events_result = service.events().list(
        calendarId='primary', 
        timeMin=now,
        maxResults=10, 
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])
    # Inside get_calendar_events
    return f"Current Date: {datetime.date.today()}. Found these events: " + str(events_result)


def create_event(summary, description, start_time, end_time, timezone):
    """
    Creates a new event on the user's Google Calendar.
    Requires a summary/title, a start ISO timestamp, an end ISO timestamp, and a timezone string.
    """
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time,
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end_time,
            'timeZone': timezone,
        },
    }

    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return f"Event created: {created_event.get('htmlLink')}"

