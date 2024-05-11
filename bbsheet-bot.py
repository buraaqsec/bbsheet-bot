import os
import csv
import argparse
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

SPREADSHEET_ID = "<Spreadsheet ID>"  # Change this to your spreadsheet ID
SERVICE_ACCOUNT_FILE = './creds.json'

# Function to get authenticated service
def get_authenticated_service():
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('sheets', 'v4', credentials=creds)

# Function to get sheet data
def get_sheet_data(sheet):
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="Sheet1!A:C").execute()
    return result.get('values', [])

# Function to append data to the sheet
def append_to_sheet(sheet, data):
    sheet_data = get_sheet_data(sheet)
    next_row = len(sheet_data) + 1
    end_row = next_row + len(data) - 1
    range_str = f"Sheet1!A{next_row}:C{end_row}"
    
    sheet.values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={
            "valueInputOption": "RAW",
            "data": [{"range": range_str, "values": data}]
        }
    ).execute()

# Function to search for a domain
def search_for_domain(service, domain):
    RANGE_NAME = "A1:D9999"
    try:
        result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])
        matches = []
        for row in values:
            if domain in row[1]:
                matches.append(row)
        return matches
    except HttpError as error:
        print(f"An error occurred: {error}")
    return None

# Function to download the sheet
def download_sheet(service):
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="A1:D9999").execute()
    values = result.get('values', [])
    with open('master_bbDomains.txt', 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(values)

# Main function
def main():
    parser = argparse.ArgumentParser(description="BB Sheet Bot to handle Bug bounty program details.")
    parser.add_argument('-s', '--search', help="Search for domain", type=str)
    parser.add_argument('-d', '--download', help="Download the complete sheet as CSV", action='store_true')
    parser.add_argument('-o', '--output', help="Output search result", action='store_true')
    parser.add_argument('-f', '--file', help="CSV file name to append data", type=str)

    args = parser.parse_args()
    service = get_authenticated_service()

    if args.search:
        matches = search_for_domain(service, args.search)
        if matches:
            for match in matches:
                date, domain_name, url = match
                print(f"Date: {date}, Domain: {domain_name}, URL: {url}")
                if args.output:
                    print(match)
        else:
            print(f"No data found for domain: {args.search}")

    if args.download:
        download_sheet(service)
        print("Sheet downloaded as master_bbDomains.csv")

    if args.file:
        sheet = service.spreadsheets()
        data_to_append = []
        with open(args.file, newline='', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                if row[1] not in [r[1] for r in get_sheet_data(sheet)]:
                    data_to_append.append(row)
        if data_to_append:
            append_to_sheet(sheet, data_to_append)

if __name__ == "__main__":
    main()
