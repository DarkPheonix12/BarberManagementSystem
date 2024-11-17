import streamlit as st
from streamlit_option_menu import option_menu
import app  # Main application module
import customer  # Customer management module
import payout  # Payout management module

class MultiApp:
    def __init__(self):
        self.apps = []

    def add_app(self, title, func):
        self.apps.append({
            "title": title,
            "function": func
        })

    def run(self):
        # Check if the user is logged in
        if not st.session_state.get("logged_in", False):
            self.login()  # Display the login page
            return  # Stop further execution if not logged in

        # If logged in, get the current page from the session state
        current_page = st.session_state.get("current_page", "Home")

        # Navbar for navigation
        selected_app = option_menu(
            menu_title='NBS Customer Management',
            options=['Home', 'Customer DB', 'Payout Management'],
            icons=['house', 'person-bounding-box', 'cash-stack'],  # Updated icons
            menu_icon='cast',  # Icon for the main menu
            default_index=0,
            orientation="horizontal",
            styles={
                "container": {"padding": "5!important", "background-color": 'black'},
                "icon": {"color": "white", "font-size": "23px"},
                "nav-link": {"color": "white", "font-size": "20px", "text-align": "center", "margin": "0px", "--hover-color": "blue"},
                "nav-link-selected": {"background-color": "#02ab21"},
            }
        )

        # Set the current page based on the user's selection
        if selected_app == "Home":
            st.session_state["current_page"] = "Home"
            app.main()  # Call the main function of the app module
        elif selected_app == "Customer DB":
            st.session_state["current_page"] = "Customer DB"
            customer.app()  # Call the main function of the customer module
        elif selected_app == "Payout Management":
            st.session_state["current_page"] = "Payout Management"
            payout.app()  # Call the payout module

    def login(self):
        def load_credentials():
            import yaml
            from yaml.loader import SafeLoader

            with open('config.yaml') as file:
                config = yaml.load(file, Loader=SafeLoader)
            return config['credentials']['usernames']

        credentials = load_credentials()

        st.title("Login Page")

        # Ensure session state keys are present
        if "logged_in" not in st.session_state:
            st.session_state["logged_in"] = False
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "login"

        username = st.text_input("Username")
        password = st.text_input("Password", type='password')

        if st.button("Login"):
            if username in credentials:
                import bcrypt  # Use bcrypt for hashing
                hashed_password = credentials[username]['password'].encode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
                    st.success("Logged in successfully!")
                    st.session_state["logged_in"] = True
                    st.session_state["current_page"] = "Home"
                    st.session_state["name"] = credentials[username]['name']  # Store user's name
                    st.rerun()  
                else:
                    st.error("Invalid username or password")
            else:
                st.error("Invalid username or password")

        if st.session_state.get("logged_in", False):
            st.write(f"You have successfully logged in as {st.session_state['name']}.")

# Create an instance of MultiApp and run it
if __name__ == "__main__":
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Home"

    multi_app = MultiApp()
    multi_app.run()
