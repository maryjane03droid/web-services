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
    #data cleaning function
    def clean_price(self, price_text):
        """
        Extract numeric price from text like '£51.77' or '€42.99'
        
        Parameters:
            price_text: String containing price with currency symbol
            
        Returns:
            Float value of the price (e.g., 51.77)
        """
        # Use regular expression to find digits and decimal points
        # \d matches any digit, \. matches decimal point, + means one or more
        price_match = re.search(r'[\d.]+', price_text)
        
        if price_match:
            # Convert matched string to float and return
            return float(price_match.group())
        else:
            # Return 0 if no price found (should not happen on this website)
            return 0.0
        #web scraping function
    def scrape_books(self, num_products=10):
        """
        Scrape book titles and prices from books.toscrape.com
        
        The website paginates results (50 books per page). This function
        will scrape across multiple pages until we have enough products.
        
        Parameters:
            num_products: Number of products to scrape (default 10)
            
        Returns:
            True if at least one product scraped, False otherwise
        """
        print(f"\n[INFO] Starting to scrape {num_products} books from {self.base_url}...")
        
        page_num = 1  # Start from page 1
        products_scraped = 0  # Counter for how many we've collected
        
        # Continue scraping until we have enough products
        while products_scraped < num_products:
            
            # Construct URL for current page
            # Page 1 has different URL pattern from subsequent pages
            if page_num == 1:
                url = f"{self.base_url}/catalogue/page-1.html"
            else:
                url = f"{self.base_url}/catalogue/page-{page_num}.html"
            
            try:
                print(f"  Accessing page {page_num}...")
                
                # Make HTTP request to the page
                response = requests.get(url, timeout=10)
                
                # Check if request was successful
                response.raise_for_status()
                
                # Parse HTML content with BeautifulSoup
                # 'html.parser' is Python's built-in HTML parser
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all book articles on the page
                # On this website, each book is inside an <article> with class 'product_pod'
                books = soup.find_all('article', class_='product_pod')
                
                # If no books found on this page, we've reached the end
                if not books:
                    print(f"  No more books found on page {page_num}")
                    break
                
                # Iterate through each book on the page
                for book in books:
                    # Stop if we've collected enough products
                    if products_scraped >= num_products:
                        break
                    
                    # ---------- EXTRACT BOOK TITLE ----------
                    # Title is inside <h3> -> <a> tag
                    # We prefer 'title' attribute as it contains full title
                    title_elem = book.find('h3').find('a')
                    title = title_elem.get('title', title_elem.text.strip())
                    
                    # ---------- EXTRACT BOOK PRICE ----------
                    # Price is in a <p> with class 'price_color'
                    price_elem = book.find('p', class_='price_color')
                    
                    if price_elem:
                        # Get the text (e.g., "£51.77") and clean it
                        original_price_text = price_elem.text.strip()
                        original_price = self.clean_price(original_price_text)
                    else:
                        # Fallback if price element not found (should not happen)
                        original_price_text = "N/A"
                        original_price = 0.0
                    
                    # ---------- STORE THE DATA ----------
                    # Create a dictionary for this product
                    product_info = {
                        'product_name': title,
                        'original_currency': 'GBP',  # Website uses British Pounds
                        'original_price_text': original_price_text,
                        'original_price_numeric': original_price
                    }
                    
                    # Add to our master list
                    self.products_data.append(product_info)
                    
                    # Increment counter
                    products_scraped += 1
                    
                    # Print progress (truncate long titles for cleaner output)
                    print(f"    [SCRAPED] {title[:50]}{'...' if len(title) > 50 else ''} - {original_price_text}")
                
                # Move to next page
                page_num += 1
                
                # Be respectful to the server - don't hammer it with requests
                # Wait 0.5 seconds before next request
                time.sleep(0.5)
                
            except requests.exceptions.RequestException as e:
                print(f"  [ERROR] Failed to access page {page_num}: {e}")
                break
            except Exception as e:
                print(f"  [ERROR] Unexpected error parsing page {page_num}: {e}")
                break
        
        # Summary of what we scraped
        print(f"\n[SUCCESS] Scraping complete! Collected {len(self.products_data)} books")
        return len(self.products_data) > 0
    
    