import requests  # For making HTTP requests to websites and APIs
from bs4 import BeautifulSoup  # For parsing HTML content and extracting data
import pandas as pd  # For creating nice tables and data manipulation
import json  # For saving data in JSON format
from datetime import datetime  # For timestamping when conversions happen
import time  # For adding delays between requests (to be respectful to servers)
import matplotlib.pyplot as plt  # For creating bar charts to visualize prices
import re 
#class  definition

class PriceScraperCurrencyConverter:
    """
    Main class that handles all functionality:
    - Scraping book data from website
    - Fetching live exchange rates
    - Converting prices
    - Displaying and saving results
    - Creating visualizations
    """
    
    def __init__(self):
        """
        Constructor method - initializes class attributes when object is created
        """
        # Base URL of the website we're scraping (no trailing slash)
        self.base_url = "http://books.toscrape.com"
        
        # List to store all scraped product data (each product is a dictionary)
        self.products_data = []
        
        # Dictionary to store exchange rates from API
        # Example: {'USD': 1.25, 'EUR': 1.15, 'KES': 150.50}
        self.exchange_rates = {}
        
        # Timestamp for when the exchange rates were fetched
        self.conversion_timestamp = None
        #exchange rate function
           
    def get_exchange_rates(self, base_currency="GBP"):
        """
        Fetch live exchange rates from free ExchangeRate-API
        
        Parameters:
            base_currency: The currency we want to convert FROM (default GBP)
        
        Returns:
            True if successful, False if failed
        """
        try:
            # Using open access endpoint - no API key required!
            # This API returns exchange rates for all currencies relative to base_currency
            url = f"https://open.er-api.com/v6/latest/{base_currency}"
            print(f"\n[INFO] Fetching exchange rates from {base_currency}...")
            
            # Make GET request to API with 10 second timeout
            # Timeout prevents the program from hanging if API is slow
            response = requests.get(url, timeout=10)
            
            # raise_for_status() will raise an exception for bad status codes (404, 500, etc.)
            response.raise_for_status()
            
            # Parse JSON response into Python dictionary
            data = response.json()
            
            # Check if API returned success status
            if data.get("result") == "success":
                # Extract the rates dictionary
                self.exchange_rates = data.get("rates", {})
                
                # Get the timestamp when rates were last updated
                self.conversion_timestamp = data.get("time_last_update_utc", 
                                                      datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
                print(f"[SUCCESS] Exchange rates fetched successfully")
                print(f"  Last update: {self.conversion_timestamp}")
                print(f"  Available currencies: {len(self.exchange_rates)} currencies")
                return True
            else:
                print(f"[ERROR] API returned error: {data.get('error-type', 'Unknown error')}")
                return False
                
        except requests.exceptions.RequestException as e:
            # Handle network-related errors (no internet, server down, etc.)
            print(f"[ERROR] Network/Request error: {e}")
            return False
        except json.JSONDecodeError as e:
            # Handle invalid JSON response
            print(f"[ERROR] Failed to parse API response: {e}")
            return False
    