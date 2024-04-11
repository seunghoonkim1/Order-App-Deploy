# Order App

The Order App is a Streamlit web application created to manage internal product orders in the company. It allows users to authenticate, browse products from a Shopify store, select items for purchase, and submit orders that will be transfered to a Google Sheets spreadsheet. Data in the Google Sheets spreadsheet is identical to the warehouse order format and therefore can be directly pasted as a bulk upload.

## Directory Structure
order_app/
├── app/
│ ├── init.py
│ └── order_app.py
├── api/
│ ├── init.py
│ ├── shopify_api.py
│ └── google_sheets.py
├── utils/
│ ├── init.py
│ └── authentication.py
├── app.py
├── config.yaml
├── requirements.txt
└── README.md

- **`app/`**: Contains main application logic.
  - `order_app.py`: Main application class for handling user interactions.


- **`api/`**: Contains modules for interacting with external APIs.
  - `shopify_api.py`: Communicates with Shopify API to retrieve product information and parsing product data.
  - `google_sheets.py`: Manages connections to Google Sheets for storing order data.

- **`utils/`**: Contains utility modules.
  - `authentication.py`: Handles user authentication.

- **`app.py`**: Script to run entire app.
- **`config.yaml`**: Configuration file for storing API keys, credentials, etc.
- **`requirements.txt`**: List of Python dependencies required to run the project.

## Getting Started

To run the Order App locally, follow these steps:

1. Clone this repository to your local machine.
2. Install the required dependencies using `pip install -r requirements.txt`.
3. Configure the `config.yaml` file with your Shopify API keys and Google Sheets credentials.
4. Run the main application script using `python app.py`.
5. Open your web browser and navigate to the provided URL to access the Order App.

For detailed instructions on setting up and using the Order App, refer to the documentation provided in the `README.md` file.

## License

This project is licensed under the [MIT License](LICENSE.txt).