import streamlit as st
import gspread
from google.oauth2 import service_account
import os
import pandas as pd
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pywhatkit as kit
from oauth2client.service_account import ServiceAccountCredentials
import time

# Conditionally import pywhatkit if not running in a headless environment
if os.environ.get('DISPLAY', '') != '':
    kit = pywhatkit  # Import pywhatkit if it's not headless
else:
    kit = None  # In headless mode, pywhatkit will not be available

# Access your GCP credentials stored in Streamlit secrets
gcp_credentials = {
    "type": "service_account",
    "project_id": st.secrets["GCP"]["GCP_PROJECT_ID"],
    "private_key": st.secrets["GCP"]["GCP_PRIVATE_KEY"],
    "client_email": st.secrets["GCP"]["GCP_CLIENT_EMAIL"],
    "client_id": st.secrets["GCP"]["GCP_CLIENT_ID"],
    "auth_uri": st.secrets["GCP"]["GCP_AUTH_URI"],
    "token_uri": st.secrets["GCP"]["GCP_TOKEN_URI"],
    "auth_provider_x509_cert_url": st.secrets["GCP"]["GCP_AUTH_PROVIDER_X509_CERT_URL"],
    "client_x509_cert_url": st.secrets["GCP"]["GCP_CLIENT_X509_CERT_URL"],
    "universe_domain": st.secrets["GCP"].get("GCP_UNIVERSE_DOMAIN", None)
}

# Authenticate with Google Sheets
def authenticate_google_sheets():
    try:
        SCOPES = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = service_account.Credentials.from_service_account_info(
            gcp_credentials, scopes=SCOPES
        )
        client = gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Error authenticating with Google Sheets: {str(e)}")
        traceback.print_exc()
        st.stop()
    return client

# Connect to a specific Google Sheet
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

# Add an appointment to the Google Sheet
def add_appointment_to_sheet(sheet, name, services, date, time, contact, offer, total_amount, referred_phone="N.A", discount_amount=0, payout_status="Unpaid"):
    try:
        services_str = ", ".join(services)
        sheet.append_row([name, services_str, date, time, contact, offer, total_amount, referred_phone, discount_amount, payout_status])
    except Exception as e:
        st.error(f"Error adding appointment to sheet: {e}")

def send_whatsapp_message(contact, message):
    # Check if DISPLAY environment variable is set (headless environment check)
    if os.environ.get('DISPLAY', '') != '':
        try:
            # Configure headless Chrome options
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            # Initialize the WebDriver with headless mode
            driver = webdriver.Chrome(options=options)

            contact_with_code = f"+91{contact}"
            kit.sendwhatmsg_instantly(contact_with_code, message, driver=driver)
            print(f"WhatsApp message sent to {contact}!")
        except Exception as e:
            print(f"Error sending WhatsApp message: {e}")
    else:
        print("WhatsApp message sending is not supported in the current environment (headless).")

def main():
    st.title("Barber Management System")
    spreadsheet_id = "1xUWgXbyIUWeEtZ3WcPKrgUbF-yH_ZCPH8PbPvtvqJsU"  # **UPDATE THIS**
    sheet = connect_to_sheet(spreadsheet_id)

    services_data = [
        {"service": "KERATIN (FEMALE)", "amount": 4200, "discount": "30%"},
        {"service": "KERATIN (MALE)", "amount": 2100, "discount": "30%"},
        {"service": "SMOOTHENING (FEMALE)", "amount": 4200, "discount": "30%"},
        {"service": "SMOOTHENING (MALE)", "amount": 1400, "discount": "30%"},
        {"service": "SCALP TREATMENT", "amount": None, "discount": None},
        {"service": "HOT OIL MASSAGE (MALE)", "amount": 140, "discount": "60%"},
        {"service": "ORGAN ALOE VERA OIL (MALE)", "amount": 140, "discount": "50%"},
        {"service": "HOT OIL MASSAGE (FEMALE)", "amount": 350, "discount": "50%"},
        {"service": "ORGAN ALOE VERA OIL (FEMALE)", "amount": 350, "discount": "50%"},
        {"service": "ANTI DANDRUFF TREATMENT (FEMALE)", "amount": 700, "discount": "30%"},
        {"service": "ANTI DANDRUFF TREATMENT (MALE)", "amount": 490, "discount": "30%"},
        {"service": "HAIR SPA L'OREAL (MALE)", "amount": 700, "discount": "30%"},
        {"service": "HAIR SPA L'OREAL (FEMALE)", "amount": 980, "discount": "30%"},
        {"service": "HAIR SPA (MALE)", "amount": 420, "discount": "30%"},
        {"service": "HAIR SPA (FEMALE)", "amount": 700, "discount": "30%"},
        {"service": "SHAMPOO CONDITIONING & STYLING (MALE)", "amount": 70, "discount": "30%"},
        {"service": "SHAMPOO CONDITIONING & STYLING (FEMALE)", "amount": 210, "discount": "30%"},
        {"service": "ROOT TOUCH UP (MALE)", " amount": 420, "discount": "30%"},
        {"service": "ROOT TOUCH UP L'OREAL (MALE)", "amount": 840, "discount": "30%"},
        {"service": "ROOT TOUCH UP AMMONIA FREE (MALE)", "amount": 1120, "discount": "30%"},
        {"service": "ROOT TOUCH UP (FEMALE)", "amount": 700, "discount": "30%"},
        {"service": "ROOT TOUCH UP L'OREAL (FEMALE)", "amount": 840, "discount": "30%"},
        {"service": "ROOT TOUCH UP AMMONIA FREE (FEMALE)", "amount": 1050, "discount": "30%"},
        {"service": "GLOBAL HAIR COLOUR (FEMALE)", "amount": 1400, "discount": "30%"},
        {"service": "GLOBAL HAIR COLOUR LOREAL (FEMALE)", "amount": 2450, "discount": "30%"},
        {"service": "GLOBAL HAIR COLOUR AMMONIA FREE (FEMALE)", "amount": 2800, "discount": "30%"},
        {"service": "GLOBAL HIGHLIGHTS (MALE)", "amount": 1400, "discount": "30%"},
        {"service": "PER STREEKS L'OREAL (MALE)", "amount": 105, "discount": "30%"},
        {"service": "GLOBAL HIGHLIGHTS (FEMALE)", "amount": 4200, "discount": "30%"},
        {"service": "PER STREEKS L'OREAL (FEMALE)", "amount": 140, "discount": "30%"},
        {"service": "HAIR CUT MALE (BASIC)", "amount": 150, "discount": "25%"},
        {"service": "HAIR CUT MALE (ADVANCE)", "amount": 175, "discount": "30%"},
        {"service": "BEARD", "amount": 70, "discount": "30%"},
        {"service": "CLEAN SHAVE", "amount": 105, "discount": "30%"},
        {"service": "HAIR TRIMMING (FEMALE)", "amount": 210, "discount": "30%"},
        {"service": "HAIR CUT ADVANCE (FEMALE)", "amount": 420, "discount": "30%"},
    ]

    # Display form to create appointments
    st.header("Create New Appointment")
    with st.form(key="appointment_form"):
        name = st.text_input("Customer Name")
        services = st.multiselect("Select Services", [s['service'] for s in services_data])
        date = st.date_input("Appointment Date")
        time = st.time_input("Appointment Time")
        contact = st.text_input("Customer Contact Number")
        offer = st.selectbox("Offer", ["None", "30% off", "50% off", "60% off"])
        total_amount = sum([s['amount'] for s in services_data if s['service'] in services])
        referred_phone = st.text_input("Referred by Phone (Optional)")
        discount_amount = st.number_input("Discount Amount", min_value=0, value=0)
        submit_button = st.form_submit_button("Submit Appointment")

        if submit_button:
            # Add appointment to Google Sheets
            add_appointment_to_sheet(sheet, name, services, date, time, contact, offer, total_amount, referred_phone, discount_amount)

            # Send WhatsApp message
            message = f"Your appointment is confirmed for {date} at {time}. Services: {', '.join(services)}. Total: {total_amount}."
            send_whatsapp_message(contact, message)

            st.success("Appointment added and WhatsApp message sent successfully.")

if __name__ == "__main__":
    main()
