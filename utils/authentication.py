import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import streamlit as st
    
class Authenticator:
    """ Login Authenticator for the streamlit app when accessing
    
    :ivar config: load login and password configuration from yaml file
    :ivar authenticator: layout configuration and use for login
    """
    
    def __init__(self):
        self.config = self.load_config()
        self.authenticator = stauth.Authenticate(
           self.config['credentials'],
           self.config['cookie']['name'],
           self.config['cookie']['key'],
           self.config['cookie']['expiry_days'],
           self.config['preauthorized']
        )
        
    def load_config(self):
        """ Load configuration from yaml file
        """
        with open('config.yaml') as file:
            config = yaml.load(file, Loader=SafeLoader)
            return config
    
    def login(self):
        """ Use authenticator and login app to main page
        """
        self.authenticator.login(location="main")
        
    def logout(self, button_name="Logout", location="main"):
        """ Use authenticator to logout of app
        :param button_name: Button of logout name will be 'Logout'
        :param location: Logout location will be main
        """
        self.authenticator.logout(button_name=button_name, location=location)
        
    def authentication_status(self):
        return st.session_state["authentication_status"]