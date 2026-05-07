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