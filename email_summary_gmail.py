# email_summary_gmail.py
# By: NathanGr33n
# Description: Authenticates with Gmail, fetches the last 10 emails, and displays basic summaries.
# Requires: Gmail API enabled, credentials.json from Google Cloud Console, and required Python packages.

from __future__ import print_function  # Ensures compatibility with Python 2/3 print function
import os.path                         # For file path checking
import base64                          # For decoding base64 email content (not used in this version)
from email.message import EmailMessage # For email message handling (not used directly in this version)
import re                              # For basic text processing (splitting sentences)

# Google API libraries
from google.oauth2.credentials import Credentials            # For loading saved user credentials
from google_auth_oauthlib.flow import InstalledAppFlow       # For managing OAuth 2.0 flow
from googleapiclient.discovery import build                  # For building Gmail service API

# Define the Gmail API scopes (what permissions we need)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    """
    Handles Gmail API authentication and returns an authorized service object.
    Loads credentials from 'token.json' if available, otherwise runs OAuth flow using 'credentials.json'.
    """
    creds = None  # Start with no credentials

    # If token.json exists, load the saved credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If credentials don't exist or are invalid, refresh or initiate login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Refresh expired credentials
        else:
            # Start a new OAuth 2.0 flow using the credentials.json file
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)  # Launch local server for Google login

        # Save the new credentials for future runs
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Return a Gmail API service object
    return build('gmail', 'v1', credentials=creds)

def fetch_last_10_emails(service):
    """
    Uses the Gmail API service to fetch the last 10 emails from the inbox.
    Extracts subject and snippet (short preview) for each email.
    """
    # List the most recent 10 messages from the user's inbox
    results = service.users().messages().list(userId='me', maxResults=10).execute()
    messages = results.get('messages', [])  # Get message metadata

    emails = []  # List to hold extracted email data

    # Loop through each message
    for msg in messages:
        # Get the full message details by ID
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()

        # Extract headers from the message payload
        headers = msg_data['payload']['headers']

        # Look for the 'Subject' header
        subject = [h['value'] for h in headers if h['name'] == 'Subject'][0]

        # Get the message snippet (Google provides a short preview of the content)
        snippet = msg_data.get('snippet', '')

        # Append subject and snippet to our list
        emails.append({'subject': subject, 'snippet': snippet})

    return emails  # Return the list of email summaries

def summarize_text(text):
    """
    Basic summarization by returning the first sentence from the input text.
    """
    # Split the text into sentences using simple punctuation
    sentences = re.split(r'[.!?]', text)

    # Return the first sentence if available, otherwise return the original text
    return sentences[0] if sentences else text

if __name__ == '__main__':
    # Authenticate and get Gmail API service
    service = authenticate_gmail()

    # Fetch the last 10 email snippets and subjects
    emails = fetch_last_10_emails(service)

    # Print a header
    print("\n=== Last 10 Email Summaries ===\n")

    # Loop through emails and print basic summaries
    for i, email in enumerate(emails, start=1):
        summary = summarize_text(email['snippet'])  # Generate summary from snippet
        print(f"{i}. {email['subject']} -> {summary}\n")  # Display subject and summary
