import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/tasks"]

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

def get_credentials():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    #if token expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    #no creds then run OAuth again
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)

        creds = flow.run_local_server(port=0)

        #same token
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds

def main():
    print("hi")
    creds = get_credentials()

    service = build("tasks", "v1", credentials=creds)

    #the thingy before the execute is our actual type of request end point thingy
    test_result = service.tasklists().list().execute()
    items = test_result.get("items", [])
    
    for item in items:
        print(f"{item['title']} : ({item['id']})")


if __name__ == "__main__":
    main()