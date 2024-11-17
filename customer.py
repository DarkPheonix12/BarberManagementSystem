import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import pandas as pd

# Function to authenticate Google Sheets
def authenticate_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    json_path = "your-credentials.json"  # Update with the correct path to your credentials JSON file

    if not os.path.exists(json_path):
        st.error(f"Credentials file not found at {json_path}. Please check the path and filename.")
        st.stop()

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
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
