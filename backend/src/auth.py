import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Absolute paths derived from this file's location — works regardless of CWD
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
_TOKEN_PATH = os.path.join(_SRC_DIR, 'token.json')
_CREDENTIALS_PATH = os.path.join(_SRC_DIR, 'credentials.json')  # fixed: was pointing one level up

def get_calendar_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists(_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(_TOKEN_PATH, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                _CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(_TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

if __name__ == "__main__":
    service = get_calendar_service()
    print("✅ Google Calendar Handshake Successful.")