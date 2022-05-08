from __future__ import print_function

import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_or_create_credentials():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '/Users/omersamet/Downloads/client_secret_835468318668-hqi7m5gvck6fs1h64eaevnv1q66ooril.apps.googleusercontent.com (1).json'
                , SCOPES)
            creds = flow.run_local_server(port=8080)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


def send_calendar_summon(title, description, start_time, end_time, attendees_mails, location, creds):
    '''
    :param title: - title of meeting - str
    :param description: - description of meeting - str
    :param start_time: starting time of meeting - str
    :param end_time: end time of meeting - str
    :param attendees_mails: all emails (str) of attendees - list(str)
    :param location: - location of event in the form "City, Hall number" - str
    :return:
            - success -> True
            - fail -> False
    '''
    try:
        service = build('calendar', 'v3', credentials=creds)
        attendees = []
        for attendee_mail in attendees_mails:
            attendees.append({'email': attendee_mail})
        event = {
            'summary': title,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'Israel',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'Israel',
            },
            'attendees': attendees,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        event = service.events().insert(calendarId='primary', body=event).execute()
        print('Event created: %s' % (event.get('htmlLink')))

    except HttpError as error:
        print('An error occurred: %s' % error)


def get_attendees_response_by_event_id(service, event_id):
    '''
    :param service: is the ctual service created before - service = build('calendar', 'v3', credentials=creds)
    :param event_id: the event id that we want to get - event['id']
    :return:
    '''
    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    response_by_attendee = defaultdict(str)
    # dict of -> attendee email: response in str
    for attendee_dict in event['attendees']:
        response_by_attendee[attendee_dict['email']] = attendee_dict['responseStatus']

    return response_by_attendee


def check_all_attendees_accept(response_by_attendee):
    for attendee_email, response_status in response_by_attendee.items():
        if response_status != 'confirmed':
            return False
    return True


if __name__ == '__main__':
    main()
