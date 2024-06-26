import requests
import time
import streamlit as st
import pandas as pd
import json

class ShopifyAPI:
    """ Initiate Shopify API
    :param base_url: shopify url for api connection
    :param endpoint: endpoint address to fetch product data with a maximum count of 250
    
    :ivar base_url: url address for shopify
    :ivar endpoint: additional address for products json
    """
    def __init__(self, base_url="https://peachandlily2.myshopify.com", endpoint="/admin/api/2024-01/products.json?limit=250"):
       self.base_url = base_url
       self.endpoint = endpoint
       self.session = self.create_session()
       
    
    def create_session(self):
        s = requests.Session()
        s.headers.update({
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": st.secrets["shopify_token"]
            })
        # important tokens and credentials are in streamlit's secret section
        # st.secrets allow streamlit to read what's in the secrets area
        # This was to prevent access for people who look at github
        
        # Everytime we get response from url, api_call will run
        s.hooks["response"] = self.api_calls
        
        return s
    
    # function to call shopify call limit
    def api_calls(self, r, *args, **kwargs):
        """ Call Shopify's call limit and maintain below limit
        :param r: reads the response when session is created
        """
        # checks the how many calls are left
        calls_left = r.headers['X-Shopify-Shop-Api-Call-Limit'].split("/")
        # call limit is 400. if 399 goes to sleep.
        if (int(calls_left[0])) == 398:
            print('limit close, sleeping')
            time.sleep(5)
    
    # Parse JSON
    def parse_json(self, resp):
        """ parse response from shopify api to json format
        :params resp: response from get of baseurl and endpoint
        """
        products = resp.json()
        product_list = pd.json_normalize(products['products'],
                                        sep="_",
                                        record_path = ['variants'],
                                        meta=['id', 'title', 'status', 'tags'],
                                        meta_prefix="parent_",
                                        record_prefix = "child_")
        return product_list

    def link_pages(self, resp):
        """ function to link pages from url. 
        link to next url using requests's links method to the header of session.
        :param resp: parse response from Shopify API
        """
        #link to next url using requests's links method to the header of session.
        next_url = resp.links['next']['url']
        return next_url
    
    def get_product_list(self):
        sess = self.create_session()
        resp = sess.get(self.base_url + self.endpoint)
        
        product_list = self.parse_json(resp)
        next_url = self.link_pages(resp)
        
        while next_url:
            print("start")
            new_response = sess.get(next_url)
            new_parse = self.parse_json(new_response)
            product_list = pd.concat([product_list, new_parse], ignore_index=True)
            try:
                next_url = self.link_pages(new_response)
            except:
                break
            else:
                next_url = self.link_pages(new_response)
        print("finish")
        
        print(product_list)
        return product_list