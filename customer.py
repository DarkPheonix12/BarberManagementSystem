import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os
import time
from requests.exceptions import ConnectionError
from google.auth.exceptions import TransportError

# Retry decorator for handling specific exceptions
def retry_on_exception(retries=3, delay=2, exceptions=(ConnectionError, TransportError)):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt < retries - 1:
                        time.sleep(delay)
                    else:
                        st.error(f"Failed after {retries} attempts: {e}")
                        raise e
        return wrapper
    return decorator

# Function to authenticate Google Sheets using Streamlit's secrets
def authenticate_google_sheets():
    # Get the credentials from Streamlit's secrets management (stored in .streamlit/secrets.toml)
    credentials_info = {
        "type": "service_account",
        "project_id": st.secrets["GCP"]["GCP_PROJECT_ID"],
        "private_key": st.secrets["GCP"]["GCP_PRIVATE_KEY"].replace('\\n', '\n'),
        "client_email": st.secrets["GCP"]["GCP_CLIENT_EMAIL"],
        "client_id": st.secrets["GCP"]["GCP_CLIENT_ID"],
        "auth_uri": st.secrets["GCP"]["GCP_AUTH_URI"],
        "token_uri": st.secrets["GCP"]["GCP_TOKEN_URI"],
        "auth_provider_x509_cert_url": st.secrets["GCP"]["GCP_AUTH_PROVIDER_X509_CERT_URL"],
        "client_x509_cert_url": st.secrets["GCP"]["GCP_CLIENT_X509_CERT_URL"],
    }

    # Define the scope for Google Sheets API
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    try:
        # Create credentials using the service account info from Streamlit's secrets
        creds = Credentials.from_service_account_info(credentials_info, scopes=scope)
        client = gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error loading or authorizing credentials: {e}")
        st.stop()

    return client

# Function to connect to the specified Google Sheet
def connect_to_sheet(spreadsheet_id, sheet_index=0):
    client = authenticate_google_sheets()
    
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        sheet = spreadsheet.get_worksheet(sheet_index)
    except gspread.SpreadsheetNotFound:
        st.error("Spreadsheet not found. Please check the Spreadsheet ID and ensure the service account has access.")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred while opening the spreadsheet: {e}")
        st.stop()

    return sheet

# Function to fetch appointments based on the provided phone number
def get_appointments(sheet, phone_number, referral=None):
    try:
        appointments = sheet.get_all_records()  # Fetch all records

        # Check if the column 'Number' exists
        if 'Number' not in appointments[0].keys():
            st.error("The 'Number' column does not exist in the sheet. Please check your sheet's column headers.")
            return []
        
        # Filter appointments by phone number
        filtered_appointments = [
            appt for appt in appointments 
            if str(appt['Number']).strip() == str(phone_number).strip()
        ]

        # Further filter by referral if specified
        if referral is not None:
            filtered_appointments = [
                appt for appt in filtered_appointments 
                if appt['Referral'].strip() == referral
            ]

        return filtered_appointments
    except Exception as e:
        st.error(f"Error fetching appointments: {e}")
        return []

# Main app function
def app():
    st.title("Customer Management")
    
    # Connect to the Google Sheets
    spreadsheet_id = "1xUWgXbyIUWeEtZ3WcPKrgUbF-yH_ZCPH8PbPvtvqJsU"  # Replace with your actual spreadsheet ID
    sheet = connect_to_sheet(spreadsheet_id)

    # Input for phone number
    phone_number = st.text_input("Enter your phone number (with country code, e.g., 918319810897):")

    # Checkbox for referrals
    referral_option = st.checkbox("Show only referrals")

    if st.button("Retrieve Appointments"):
        if phone_number:  # Check if the phone number is provided
            # Get appointments based on the phone number and referral option
            appointments = get_appointments(sheet, phone_number, "Yes" if referral_option else None)

            if appointments:
                # Convert to DataFrame for better display
                df = pd.DataFrame(appointments)
                st.table(df)  # Display all appointment details in tabular form
            else:
                st.error("No appointments found for this phone number.")
        else:
            st.error("Please enter a valid phone number.")

# Run the app
if __name__ == "__main__":
    app()
