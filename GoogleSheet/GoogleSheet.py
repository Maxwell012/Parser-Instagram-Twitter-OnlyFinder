import os.path
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import SPREADSHEET_ID


class GoogleSheet:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    service = None

    def __init__(self):
        creds = None
        if os.path.exists('GoogleSheet/token.pickle'):
            with open('GoogleSheet/token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print('flow')
                flow = InstalledAppFlow.from_client_secrets_file('GoogleSheet/credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open('GoogleSheet/token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('sheets', 'v4', credentials=creds)

    def append_range_values(self, range_, values):
        body = {'values': values}
        result = self.service.spreadsheets().values().append(spreadsheetId=SPREADSHEET_ID,
                                                             range=range_,
                                                             valueInputOption="USER_ENTERED",
                                                             insertDataOption="INSERT_ROWS",
                                                             includeValuesInResponse=True,
                                                             body=body).execute()
        updated_range = result['updates']['updatedRange']
        return updated_range

    def get_range_values(self, range_):
        result = self.service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=range_).execute()
        values = result.get('values', [])
        return values
