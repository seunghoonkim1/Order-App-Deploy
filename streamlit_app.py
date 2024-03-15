import streamlit as st
from streamlit_gsheets import GSheetsConnection
import streamlit_authenticator as stauth
import pandas as pd
from datetime import date, datetime
import yaml
from yaml.loader import SafeLoader
import requests
import json
import time

## ESTABLISHING CONNECTION - SHOPIFY
base_url = "https://peachandlily2.myshopify.com"
endpoint = "/admin/api/2024-01/products.json?limit=250"

# function to create Shopify Session
def create_session():
        s = requests.Session()
        s.headers.update({
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": st.secrets["shopify_token"]
            }) # st.secrets allow streamlit to read what's in the secrets area
    
        # function to call shopify call limit
        def api_calls(r, *args, **kwargs):
            # checks the how many calls are left
            calls_left = r.headers['X-Shopify-Shop-Api-Call-Limit'].split("/")
            # call limit is 400. if 399 goes to sleep.
            if (int(calls_left[0])) == 398:
                print('limit close, sleeping')
                time.sleep(5)
        
        # Everytime we get response from url, api_call will run
        s.hooks["response"] = api_calls
        
        return s

# Parse JSON
def parse_json(resp):
    products = resp.json()
    product_list = pd.json_normalize(products['products'],
                                    sep="_",
                                    record_path = ['variants'],
                                    meta=['id', 'title', 'status', 'tags'],
                                    meta_prefix="parent_",
                                    record_prefix = "child_")
    return product_list

# function to link pages from url
def link_pages(resp):
    #link to next url using requests's links method to the header of session.
    next_url = resp.links['next']['url']
    return next_url

# function to read the main script for creating shopify session
def main():
    sess = create_session()
    resp = sess.get(base_url + endpoint)
    
    product_list = parse_json(resp)
    next_url = link_pages(resp)
    
    while next_url:
        print("start")
        new_response = sess.get(next_url)
        new_parse = parse_json(new_response)
        product_list = pd.concat([product_list, new_parse], ignore_index=True)
        try:
            next_url = link_pages(new_response)
        except:
            break
        else:
            next_url = link_pages(new_response)
    print("finish")
    
    return product_list    

# initiate Shopify connection
data = main()

# filter to active products
data = data[data["parent_status"] == "active"]
# isolate only needed columns
data = data[["child_sku", "parent_title", "child_inventory_quantity", "parent_tags"]]
# rename columns
data.rename(columns={"child_sku":"SKU", "parent_title":"product", "child_inventory_quantity":"in_stock", "parent_tags":"tags"}, inplace=True)
# title list without limitation
p_title_list = list(set(data["product"]))
# sku list without limitation
sku_list = list(set(data['SKU']))
# title list for marketing
marketing_data = data[data["tags"].str.contains(r"Marketing")]
marketing_title_list = list(set(marketing_data["product"]))
# sku list for marketing
marketing_sku_list = list(set(marketing_data["SKU"]))

## APP DESIGN
## SETUP LOGIN WINDOW
users = ["marketing", "peach"]
usernames = ["marketing", "peach"]

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
    )

authenticator.login(location="main")

if st.session_state["authentication_status"] is False:
    st.error("Username/Password is incorrect")

elif st.session_state["authentication_status"] is None:
    st.error("Please enter your username and password")

elif st.session_state["authentication_status"]:
    ## ESTABLISHING CONNECTION - GOOGLE SHEETS
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Fetch existing data
    existing_data = conn.read(worksheet="Sheet1")
    existing_data = existing_data.dropna(how="all")
    existing_order_list = set(existing_data['Sales order number *'])

    ## Logout button
    authenticator.logout(button_name="Logout", location="main")

    ## Display Title and Description
    st.title("Peach and Lily - Order Portal")
    st.markdown("Enter the details of the order below.")
    st.text("* is required")

    ## Initiate Session State (Page)
    if 'Department' not in st.session_state:
        st.session_state["Department"] = ""
        st.session_state["customer_name"] = ""
        st.session_state["address_1"] = ""
        st.session_state["address_2"] = ""
        st.session_state["company_name"] = ""
        st.session_state["city_name"] = ""
        st.session_state["state_name"] = ""
        st.session_state["zip_code"] = ""
        st.session_state["country"] = ""
        st.session_state["email"] = ""
        

    ## First Container - information on ordering department and order number generation

    with st.container(border = True):
        st.subheader("Department")
        department_list = ["Marketing", "Sales", "Operations", "Finance"]
        ordering_department = st.selectbox("Choose Ordering Department",
                                        department_list)
        # Add to Session State
        st.session_state["Department"] = ordering_department

    ## Order Number Creating
    department_list = {"Marketing":"MKT", 
                    "Sales":"SLS",
                    "Operations":"OPS",
                    "Finance":"FIN"}
    number_start = 1
    sales_order_number = department_list[ordering_department] + str(date.today().strftime("%m%d%y")) + str(number_start)
    for sales_order_number in existing_order_list:
        number_start +=1
        sales_order_number = department_list[ordering_department] + str(date.today().strftime("%m%d%y")) + str(number_start)

    ## Second Container - order items
    with st.container(border = True):
        st.subheader("Items")
        cols = st.columns([2,1,1])
        dep_list = ["MKT", "SLS"]
        if department_list[ordering_department] not in dep_list:
            title_list = p_title_list
        else:
            title_list = marketing_title_list
        product = cols[0].selectbox("Select product*", title_list, index=None, placeholder="select product", key="productselect")
        linked_sku = data.loc[data["product"]== product, "SKU"]
        order_sku = cols[1].selectbox("Select sku", options=linked_sku, index=None, placeholder="select sku", key="skuselect")
        quantity = cols[2].text_input("Enter quantity*", " ", key="quantitykeyed")

        # Button to add item
        add_item_button = st.button("Add Item")
        if add_item_button:
                if int(data.loc[data["product"] == product, "in_stock"].item()) * 0.1 > int(quantity):
                    if product and order_sku:
                        st.session_state["product"].append(product)
                        st.session_state['SKU'].append(order_sku)
                        st.session_state["quantity"].append(int(quantity)) 
                    else:
                        st.warning("Ensure product and sku are selected")
                        st.stop()
                else:
                    st.warning("Product out of stock")
                    st.stop()
                    
        # Ordered items in a detailed table
        # assigning grid
        grid = st.columns([2,1,1,1])
        
        # Initiate session state
        if "product" not in st.session_state:
            st.session_state["product"] = []
            st.session_state["SKU"] = []
            st.session_state["quantity"] = []
            
        if st.session_state["product"]:
            grid[0].text("product")
            grid[1].text("SKU")
            grid[2].text("quantity")
        
        def reset_item():
            st.session_state["product"].remove(p)
            st.session_state["SKU *"].remove(s)
            st.session_state["quantity"].remove(q)
        
        # loop to iterate each line of product ordered
        i=0
        for p,s,q in zip(st.session_state["product"], st.session_state['SKU'], st.session_state['quantity']):
            grid_1 = st.columns([2,1,1,1])
            grid_1[0].write(p)
            grid_1[1].write(s)
            grid_1[2].write(q)
            grid_1[3].button("remove", on_click = reset_item, key=f"order{i}")
            i+=1


    ## Third Container - customer information & Shipment Details
    # Onboarding new order
    with st.form("customer information", clear_on_submit=True):
        # CUSTOMER INFORMATION
        st.subheader("Ship To")
        customer_name = st.text_input(label="Customer Name*")
        address_1 = st.text_input(label="Shipping Address Line 1*")
        address_2 = st.text_input(label="Shipping Address Line 2")
        company_name = st.text_input(label="Company")
        city_name = st.text_input(label="City*")
        state_name = st.text_input(label="State*")
        zip_code = st.text_input(label="ZIP Code*")
        country = st.text_input(label="Country*")
        email = st.text_input(label="email*")
        
        # Include values in session state
        #st.session_state["customer_name"] = customer_name
        #st.session_state["address_1"] = address_1
        #st.session_state["address_2"] = address_2
        #st.session_state["company_name"] = company_name
        #st.session_state["city_name"] = city_name
        #st.session_state["state_name"] = state_name
        #st.session_state["zip_code"] = zip_code
        #st.session_state["country"] = country
        #st.session_state["email"] = email

        # SHIPMENT INFORMATION
        st.subheader("Shipment Detail")
        # Options on selecting which shipment method will be used
        shipping_method = st.selectbox("Choose Shipping Method",
                                    ("FedEx Ground", "FedEx 2Day", "FedEx Standard Overnight"), 
                                    index=None,
                                    placeholder="Select method")
        
        # Option on selecting the urgency of shipment
        priority = st.selectbox("Choose Priority",
                                ("Medium", "High"),
                                index=None,
                                placeholder="Select priority")
        
        # Option on selecting when this should be sent out
        ship_by = st.date_input(label="Ship By")
        
        # Checking to see if shipment should be B2B or D2C
        if sum(st.session_state["quantity"]) >= 100:
            order_channel = "B2B"
        else:
            order_channel = "D2C"

        # Initiate order_data dictionary to avoid error
        order_data = {}
        order_items = st.session_state

        ## SUBMIT BUTTON
        submitted = st.form_submit_button("Submit")
        # if the submit button is pressed
        if submitted:
            # Check if all mandatory filed are filled
            if not customer_name or not address_1 or not city_name or not state_name or not zip_code or not country or not email:
                st.warning("Ensure all mandatory fields are filled")
                st.stop()
            else:
                # Create a new row of order data
                order_data = {
                "Channel *": order_channel,
                "Sales order number *": sales_order_number,
                "Custom order reference": "",
                "Do not ship before": "",
                "Ship by": ship_by.strftime("%m/%d/%y"),
                "Priority *": priority,
                "Notes": "",
                "Gift message": "",
                "Customer name *": customer_name,
                "Address line 1 *": address_1,
                "Address line 2": address_2,
                "Company": company_name,
                "City *": city_name,
                "State *": state_name,
                "Zip code *": zip_code,
                "Country *": country,
                "Email *": email,
                "Contact phone": "",
                "Service method": shipping_method,
                "Unit of measure *": "ea",
                "Lot": "",
                "Sale price": "",
                "Origin facility *": "BDLS001",
                "Shipment Type": "Parcel"
                }

                ## DATAFRAME CLEANING
                # Create Dataframe
                order_item_df = pd.DataFrame([order_items])
                order_data_df = pd.DataFrame([order_data])
                
                # Rename columns
                orders = pd.concat([order_data_df, order_item_df], axis=1)
                orders = orders.rename(columns={"SKU": "SKU *", "quantity": "Quantity ordered *"})
                orders = orders[[
                    "Channel *",
                    "Sales order number *",
                    "Custom order reference",
                    "Do not ship before",
                    "Ship by",
                    "Priority *",
                    "Notes",
                    "Gift message",
                    "Customer name *",
                    "Address line 1 *",
                    "Address line 2",
                    "Company",
                    "City *",
                    "State *",
                    "Zip code *",
                    "Country *",
                    "Email *",
                    "Contact phone",
                    "Service method",
                    "SKU *",
                    "Quantity ordered *",
                    "Unit of measure *",
                    "Lot",
                    "Sale price",
                    "Origin facility *",
                    "Shipment Type"
                    ]]
                
                # use pd.explode(list("columns")) to split multiple items in cell
                orders = orders.explode(["SKU *", "Quantity ordered *"])

                # Last check with dataframe.
                #st.dataframe(data=orders)

                # Add the new order data to the existing data
                updated_df = pd.concat([existing_data, orders], ignore_index=True)

                # Update Google Sheets with the new order data
                conn.update(worksheet="Sheet1", data=updated_df)
            
            st.write(f"Order Sumbitted! Order Number is {sales_order_number}")