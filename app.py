import streamlit as st
import gspread
from google.oauth2 import service_account
from oauth2client.service_account import ServiceAccountCredentials
import os
import pandas as pd
import time
import traceback
import requests
from twilio.rest import Client

# Conditionally import pywhatkit if not running in a headless environment
if os.environ.get('DISPLAY', '') != '':
    import pywhatkit as kit
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

# Send WhatsApp message via Twilio
def send_whatsapp_message_via_twilio(to_number, message):
    try:
        # Twilio credentials from Streamlit secrets
        TWILIO_ACCOUNT_SID = st.secrets["TWILIO"]["ACCOUNT_SID"]
        TWILIO_AUTH_TOKEN = st.secrets["TWILIO"]["AUTH_TOKEN"]
        TWILIO_WHATSAPP_NUMBER = st.secrets["TWILIO"]["WHATSAPP_NUMBER"]  # Format: 'whatsapp:+14155238886'

        # Initialize the Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # Send WhatsApp message
        message = client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_NUMBER,  # Twilio's WhatsApp-enabled number
            to=f'whatsapp:+91{to_number}'  # Adjust the country code as needed
        )

        st.success(f"WhatsApp message sent to {to_number}! Message SID: {message.sid}")
    except Exception as e:
        st.error(f"An error occurred while sending WhatsApp message via Twilio: {e}")

def main():
    st.title("Barber Management System")
    spreadsheet_id = "1xUWgXbyIUWeEtZ3WcPKrgUbF-yH_ZCPH8PbPvtvqJsU"  # **UPDATE THIS**
    sheet = connect_to_sheet(spreadsheet_id)

    services_data = [
        {"service": "KERATIN (FEMALE)", "amount": 4200, "discount": "30%"},
        {"service": "KERATIN (MALE)", "amount": 2100, "discount": "30%"},
        {"service": "SMOOTHENING (FEMALE)", "amount": 4200, "discount": "30%"},
        {"service": "SMOOTHENING (MALE)", "amount": 1400, "discount": "30%"},
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
        {"service": "HAIR CUT ADVANCE (FEMALE)", "amount": 350, "discount": "30%"},
        {"service": "CREATIVE HAIR CUT (FEMALE)", "amount": 420, "discount": "30%"},
        {"service": "BABY HAIR CUT BASIC", "amount": 105, "discount": "30%"},
        {"service": "BABY HAIR CUT ADVANCE", "amount": 150, "discount": "25%"},
        {"service": "LOTUS BASIC FACIAL", "amount": 700, "discount": "30%"},
        {"service": "RAAGA FACIAL", "amount": 700, "discount": "30%"},
        {"service": "NATURES FACIAL", "amount": 700, "discount": "30%"},
        {"service": "GLODSHEEN FACIAL", "amount": 1540, "discount": "30%"},
        {"service": "RAGA PLATINUM FACIAL", "amount": 1400, "discount": "30%"},
        {"service": "RAGA GOLD FACIAL", "amount": 1400, "discount": "30%"},
        {"service": "FRESH FRUIT FACIAL", "amount": 1400, "discount": "30%"},
        {"service": "O3+ WHITENING", "amount": 1750, "discount": "30%"},
        {"service": "O3+ SEAWEED", "amount": 1750, "discount": "30%"},
        {"service": "LOTUS 4 LAYERS", "amount": 1750, "discount": "30%"},
        {"service": "CHENYI'S TAN CLEAR", "amount": 1750, "discount": "30%"},
        {"service": "CHENYI'S SENSIGLOW", "amount": 1750, "discount": "30%"},
        {"service": "O3+ DIAMOND", "amount": 1750, "discount": "30%"},
        {"service": "ANTI AGEING (LOTUS)", "amount": 1750, "discount": "30%"},
        {"service": "Cream Bleach FACE", "amount": 420, "discount": "30%"},
        {"service": "Cream Bleach NECK", "amount": 280, "discount": "30%"},
        {"service": "Cream Bleach UNDER ARMS", "amount": 140, "discount": "30%"},
        {"service": "Cream Bleach FULL BACK", "amount": 560, "discount": "30%"},
        {"service": "Cream Bleach HALF ARM", "amount": 210, "discount": "30%"},
        {"service": "Cream Bleach FULL ARM", "amount": 420, "discount": "30%"},
        {"service": "Cream Bleach FEET", "amount": 280, "discount": "30%"},
        {"service": "Cream Bleach HALF LEG", "amount": 420, "discount": "30%"},
        {"service": "Cream Bleach FULL LEG", "amount": 700, "discount": "30%"},
        {"service": "Cream Bleach FULL BODY", "amount": 2800, "discount": "30%"},
        {"service": "LUXURY FULL BODY MASSAGE", "amount": 2100, "discount": "30%"},
        {"service": "CLEAN-UP O3", "amount": 700, "discount": "0%"},
        {"service": "CLEAN-UP LOTUS", "amount": 350, "discount": "0%"},
        {"service": "CLEAN-UP NATURES", "amount": 350, "discount": "0%"},
        {"service": "MENICURES BASIC", "amount": 630, "discount": "30%"},
        {"service": "MENICURES CLASSIC", "amount": 700, "discount": "30%"},
        {"service": "MENICURES LUXURY", "amount": 1050, "discount": "30%"},
        {"service": "PEDICURES BASIC", "amount": 700, "discount": "30%"},
        {"service": "PEDICURES CLASSIC", "amount": 910, "discount": "30%"},
        {"service": "PEDICURES LUXURY", "amount": 1400, "discount": "30%"}
    ]

    st.subheader("Add New Appointment")
    with st.form(key="appointment_form"):
        name = st.text_input("Customer Name")
        services_selected = st.multiselect("Select Services", [service["service"] for service in services_data])
        date = st.date_input("Appointment Date")
        time = st.time_input("Appointment Time")
        contact = st.text_input("Customer Contact (10-digit number for India only)")
        offer = st.selectbox("Avail Offer?", ["No", "Yes"])
        payout_status = st.selectbox("Payout Status", ["Unpaid", "Paid"])
        referred_phone = st.text_input("Referred Phone Number", value="N.A")
        discount_percentage = st.number_input("Percentage of Services Availment", min_value=0, max_value=100, value=20)
        submit_button = st.form_submit_button(label="Add Appointment")

        if submit_button:
            if not name or not services_selected or not time or not contact:
                st.error("Please fill in all fields.")
                return
            if not contact.isdigit() or len(contact) != 10:
                st.error("Please enter a valid 10-digit phone number.")
                return
            total_amount = sum(service["amount"] for service in services_data if service["service"] in services_selected)
            discount_amount = 0
            if offer == "Yes" and referred_phone != "N.A":
                discount_amount = (discount_percentage / 100) * total_amount
                st.write(f"Discount Amount: {discount_amount} ")
            contact_with_code = f"+91{contact}"
            time_str = time.strftime("%H:%M")
            date_str = date.strftime("%Y-%m-%d")
            add_appointment_to_sheet(sheet, name, services_selected, date_str, time_str, contact_with_code, offer, total_amount, referred_phone, discount_amount, payout_status)
            message = (
                f"Hello {name},\n\n"
                "Thank you for visiting us at our Nature's Beauty Salon! We hope you had an amazing experience with our services.\n"
                "We'd love for you to leave us a great review on Google! "
                "Your feedback helps us improve and lets others know about the excellent service we provide.\n\n"
                "Looking forward to seeing you again!\n\n"
                "Best regards,\nThe Salon Team"
            )
            send_whatsapp_message(contact, message)
            st.success(f"Appointment added successfully for {name}. Payout Status: {payout_status}")

    st.subheader("All Appointments")
    try:
        appointments = sheet.get_all_records()
        if not appointments:
            st.write("No appointments found.")
        else:
            df = pd.DataFrame(appointments)
            if 'Payout Status' in df.columns:
                df['Payout Status'] = df['Payout Status'].replace({'True': 'Paid', 'False': 'Unpaid'})
            st.table(df)
    except Exception as e:
        st.error(f"Error fetching appointments: {e}")

if __name__ == "__main__":
    main()
