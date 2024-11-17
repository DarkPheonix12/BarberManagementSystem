import streamlit as st 
import yaml
from yaml.loader import SafeLoader
import bcrypt  # Use bcrypt for hashing


def app():
    st.title("Customer Management")
    st.write("This is the customer management section.")