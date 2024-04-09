import streamlit as st
from streamlit_gsheets import GSheetsConnection

class GoogleSheets:
    """ Connecting Google Sheets API with Streamlit
    :param connection: connection configuration
    
    :ivar conn: establish connection
    """
    def __init__(self, connection):
        self.conn = connection
    
    def read_existing_data(self, worksheet):
        """ Pull existing data on Google Sheet
        :param worksheet: specify worksheet to read
        """
        existing_data = self.conn.read(worksheet=worksheet)
        existing_data = existing_data.dropna(how="all")
        return existing_data
    
    def update_data(self, worksheet, data):
        """ Push new data onto Google Sheet
        :param worksheet: specify worksheet to update
        :param data: new data to add to worksheet
        """
        self.conn.update(worksheet=worksheet, data=data)