import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import os
import pandas as pd
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

# Authentication function with enhanced retry handling for Google Sheets API
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

# Connect to the specified Google Sheet
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

# Normalize phone numbers to a standard format
def normalize_phone_number(phone):
    phone = ''.join(filter(str.isdigit, phone))
    if len(phone) == 10:
        return f"+91{phone}"
    elif len(phone) == 12 and phone.startswith("91"):
        return f"+{phone}"
    return phone

# Fetch payout information based on a referred phone number
@retry_on_exception(retries=3, delay=2)
def fetch_payouts(sheet, referred_phone):
    normalized_referred_phone = normalize_phone_number(referred_phone)
    records = sheet.get_all_records()
    total_unpaid = 0
    total_paid = 0
    unpaid_entries = []
    paid_entries = []

    for idx, record in enumerate(records):
        referred_by = normalize_phone_number(str(record.get('Referred By', '')).strip())
        payout_status = str(record.get('Payout Status', '')).strip().lower()
        payout_value = record.get('Payout', 0) or 0

        if referred_by == normalized_referred_phone:
            if payout_status == "unpaid":
                total_unpaid += payout_value
                unpaid_entries.append((idx + 2, record))  # Adjust for 1-based indexing
            elif payout_status == "paid":
                total_paid += payout_value
                paid_entries.append((idx + 2, record))  # Adjust for 1-based indexing

    return total_unpaid, total_paid, unpaid_entries, paid_entries

# Update a single cell in the sheet with retry logic
@retry_on_exception(retries=3, delay=2)
def update_single_cell(sheet, row, col, value):
    try:
        sheet.update_cell(row, col, value)
        return True
    except Exception as e:
        st.error(f"Error updating cell at row {row}, col {col}: {str(e)}")
        return False

# Update the payout status of entries in the sheet
@retry_on_exception(retries=3, delay=2)
def update_payout_status(sheet, matched_entries, new_status):
    if not matched_entries:
        return False

    try:
        headers = sheet.row_values(1)  # Get the first row as headers
        st.write(f"Headers found: {headers}")  # Debugging: Check headers
        status_col = None

        # Match column for 'Payout Status'
        for idx, header in enumerate(headers, 1):
            if header.strip().lower() == 'payout status':  # Case-insensitive check
                status_col = idx
                break

        if status_col is None:
            st.error("Could not find 'Payout Status' column")
            return False

        success_count = 0
        for row_idx, _ in matched_entries:
            if update_single_cell(sheet, row_idx, status_col, new_status):
                success_count += 1
            time.sleep(0.5)  # Avoid rate limits

        if success_count > 0:
            st.success(f"Successfully updated {success_count} entries to {new_status}")
            return True
        else:
            st.warning("No entries were updated")
            return False

    except Exception as e:
        st.error(f"Error in update_payout_status: {str(e)}")
        return False

# Main application function
def app():
    st.title("Payout Management")

    referred_phone = st.text_input("Enter Referred Phone Number")

    if st.button("Get Payout"):
        if not referred_phone:
            st.error("Please enter a phone number.")
            return

        spreadsheet_id = "1xUWgXbyIUWeEtZ3WcPKrgUbF-yH_ZCPH8PbPvtvqJsU"
        sheet = connect_to_sheet(spreadsheet_id)

        try:
            total_unpaid, total_paid, unpaid_entries, paid_entries = fetch_payouts(sheet, referred_phone)
        except (ConnectionError, TransportError) as e:
            st.error(f"Connection error while fetching payouts: {e}")
            return

        if total_unpaid > 0 or total_paid > 0:
            st.success(f"Total Unpaid Payout for {referred_phone}: ₹{total_unpaid}")
            st.success(f"Total Paid Payout for {referred_phone}: ₹{total_paid}")

            st.subheader("Unpaid Entries:")
            if unpaid_entries:
                df_unpaid = pd.DataFrame([entry[1] for entry in unpaid_entries])
                st.dataframe(df_unpaid)
            else:
                st.write("No unpaid entries found.")

            st.subheader("Paid Entries:")
            if paid_entries:
                df_paid = pd.DataFrame([entry[1] for entry in paid_entries])
                st.dataframe(df_paid)
            else:
                st.write("No paid entries found.")
