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
    #currency conversion function
    
    def convert_prices(self, target_currency="KES"):
        """
        Convert all scraped prices to target currency
        
        Parameters:
            target_currency: 3-letter currency code (e.g., 'KES', 'USD', 'EUR')
            
        Returns:
            True if successful, False if rates not available or currency invalid
        """
        # Check if we have exchange rates loaded
        if not self.exchange_rates:
            print("[ERROR] No exchange rates available. Please fetch rates first.")
            return False
        
        # Verify target currency exists in our rates
        if target_currency not in self.exchange_rates:
            print(f"[ERROR] Currency '{target_currency}' not found in exchange rates")
            print(f"  Available currencies: {list(self.exchange_rates.keys())[:20]}...")
            return False
        
        # Get conversion rate (how much target currency equals 1 GBP)
        conversion_rate = self.exchange_rates[target_currency]
        
        print(f"\n[INFO] Converting prices from GBP to {target_currency}")
        print(f"  Exchange rate: 1 GBP = {conversion_rate:.4f} {target_currency}")
        
        # Loop through each product and add converted price
        for product in self.products_data:
            # Get original price (in GBP)
            original_price = product['original_price_numeric']
            
            # Calculate converted price
            converted_price = original_price * conversion_rate
            
            # Add conversion information to product dictionary
            product['target_currency'] = target_currency
            product['converted_price_numeric'] = round(converted_price, 2)
            product['converted_price_text'] = f"{product['target_currency']} {converted_price:.2f}"
            product['exchange_rate_used'] = conversion_rate
        
        print(f"[SUCCESS] Converted {len(self.products_data)} prices to {target_currency}")
        return True
    #display table functionfunction


    def display_table(self):
        """
        Display products in a nicely formatted table using pandas
        
        Creates a clean, readable table showing product names and prices
        both in original and converted currencies.
        """
        # Guard clause - check if we have data
        if not self.products_data:
            print("No data to display")
            return
        
        # Convert our list of dictionaries to pandas DataFrame
        # DataFrames are like spreadsheets in Python
        df = pd.DataFrame(self.products_data)
        
        # Select only the columns we want to show and rename them
        # .copy() creates a new DataFrame to avoid modifying original
        display_df = df[['product_name', 'original_price_text', 'converted_price_text']].copy()
        display_df.columns = [
            'Product Name', 
            f'Original (GBP)', 
            f'Converted ({df["target_currency"].iloc[0] if len(df) > 0 else "Target"})'
        ]
        
        # Print formatted table with separators
        print("\n" + "="*100)
        print(" " * 35 + "SCRAPED PRODUCTS WITH CONVERTED PRICES")
        print("="*100)
        
        # to_string() creates a text-based table
        # index=False hides the row numbers
        print(display_df.to_string(index=False))
        
        print("="*100)
        
        # ---------- CALCULATE AND DISPLAY STATISTICS ----------
        if 'original_price_numeric' in df.columns and 'converted_price_numeric' in df.columns:
            print(f"\n📊 SUMMARY STATISTICS:")
            print(f"  • Total Products Scraped: {len(df)}")
            print(f"  • Original Price Range: {df['original_price_numeric'].min():.2f} - {df['original_price_numeric'].max():.2f} GBP")
            print(f"  • Converted Price Range: {df['converted_price_numeric'].min():.2f} - {df['converted_price_numeric'].max():.2f} {df['target_currency'].iloc[0]}")
            print(f"  • Average Original Price: {df['original_price_numeric'].mean():.2f} GBP")
            print(f"  • Average Converted Price: {df['converted_price_numeric'].mean():.2f} {df['target_currency'].iloc[0]}")
    
    #data saving function
def save_to_csv(self, filename="product_prices.csv"):
        """
        Save scraped and converted data to CSV file
        
        CSV (Comma-Separated Values) is easily readable by Excel, Google Sheets, etc.
        
        Parameters:
            filename: Name of the CSV file to create (default: product_prices.csv)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.products_data:
            print("[ERROR] No data to save")
            return False
        
        # Convert to DataFrame for easy CSV export
        df = pd.DataFrame(self.products_data)
        
        # Save to CSV (comma-separated values)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"\n[SAVED] Data exported to {filename}")
        
        # Also save metadata (information about the conversion)
        # This is separate because CSV doesn't support nested data well
        metadata = {
            'conversion_timestamp': self.conversion_timestamp,
            'exchange_rates_used': {
                self.products_data[0]['target_currency']: self.products_data[0]['exchange_rate_used']
            } if self.products_data else {},
            'total_products': len(self.products_data),
            'scrape_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'source_website': self.base_url
        }
        
        # Save metadata as JSON
        with open('conversion_metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"[SAVED] Metadata saved to conversion_metadata.json")
        
        return True
    
def save_to_json(self, filename="product_prices.json"):
        """
        Save scraped and converted data to JSON file with metadata
        
        JSON (JavaScript Object Notation) preserves data structure and is
        great for APIs and data exchange.
        
        Parameters:
            filename: Name of the JSON file to create (default: product_prices.json)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.products_data:
            print("[ERROR] No data to save")
            return False
        
        # Create a comprehensive data structure with metadata at the top
        output_data = {
            'scrape_info': {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'conversion_timestamp': self.conversion_timestamp,
                'total_products': len(self.products_data),
                'source_url': self.base_url,
                'exchange_rate_source': 'ExchangeRate-API (open.er-api.com)'
            },
            'products': self.products_data  # List of product dictionaries
        }
        
        # Write to JSON file with indentation for readability
        # ensure_ascii=False allows special characters (like £) to display properly
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"[SAVED] Data exported to {filename}")
        return True
#visualization function
def plot_prices(self):
        """
        Create a bar chart comparing original vs converted prices
        
        Uses matplotlib to generate a professional-looking visualization
        that makes it easy to see the price differences.
        """
        if not self.products_data:
            print("[ERROR] No data to plot")
            return
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(self.products_data)
        
        # Limit to first 10 products (or fewer if we have less)
        # Bar charts get cluttered with too many items
        products_to_plot = min(10, len(df))
        
        # Extract data for plotting
        product_names = df['product_name'].head(products_to_plot).tolist()
        original_prices = df['original_price_numeric'].head(products_to_plot).tolist()
        converted_prices = df['converted_price_numeric'].head(products_to_plot).tolist()
        
        # Get target currency for labeling
        target_currency = df['target_currency'].iloc[0]
        exchange_rate = df['exchange_rate_used'].iloc[0]
        
        # ---------- CREATE THE FIGURE AND AXES ----------
        # fig: the whole figure/window
        # ax: the actual plot area (subplot)
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # ---------- SET UP BAR POSITIONS ----------
        # x coordinates for where bars will be placed
        x = range(len(product_names))
        
        # Width of each bar (0.35 leaves gaps between grouped bars)
        width = 0.35
        
        # Create the bars
        # Bars for original prices (place slightly left of center)
        bars1 = ax.bar([i - width/2 for i in x], original_prices, width, 
                       label=f'Original (GBP)', 
                       color='skyblue', 
                       alpha=0.8)  # alpha = transparency (0=invisible, 1=opaque)
        
        # Bars for converted prices (place slightly right of center)
        bars2 = ax.bar([i + width/2 for i in x], converted_prices, width,
                       label=f'Converted ({target_currency})', 
                       color='lightcoral', 
                       alpha=0.8)
        
        # ---------- CUSTOMIZE THE CHART ----------
        # Set title (with multi-line formatting)
        ax.set_title(f'📊 Product Price Comparison: GBP vs {target_currency}\n'
                    f'Exchange Rate: 1 GBP = {exchange_rate:.4f} {target_currency}',
                    fontsize=14, 
                    fontweight='bold',
                    pad=20)  # pad = padding above title
        
        # Label the axes
        ax.set_xlabel('Product Name', fontsize=11, fontweight='bold')
        ax.set_ylabel('Price', fontsize=11, fontweight='bold')
        
        # Set x-axis tick labels (product names)
        ax.set_xticks(x)
        ax.set_xticklabels(product_names, rotation=45, ha='right', fontsize=9)
        
        # Add a legend (shows what colors represent)
        ax.legend(loc='upper right', fontsize=10)
        
        # Add grid lines for easier value reading (only horizontal)
        ax.grid(True, alpha=0.3, axis='y', linestyle='--')
        
        # Set y-axis to start at 0 for accurate comparison
        ax.set_ylim(bottom=0)
        
        # ---------- ADD VALUE LABELS ON BARS ----------
        # This shows the actual price numbers on top of each bar
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                # Text placement: x at bar center, y at bar height + small offset
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}',  # Format with 1 decimal place
                       ha='center',      # Horizontal alignment: center
                       va='bottom',      # Vertical alignment: bottom (above bar)
                       fontsize=8,
                       fontweight='bold')
        
        # Adjust layout to prevent labels from being cut off
        plt.tight_layout()
        
        # ---------- SAVE THE CHART ----------
        # Save as PNG with high DPI (dots per inch) for quality
        plt.savefig('price_comparison_chart.png', dpi=300, bbox_inches='tight')
        print(f"\n[SAVED] Chart saved as 'price_comparison_chart.png'")
        
        # ---------- DISPLAY THE CHART ----------
        # Show the plot in a window (will pause script until closed)
        plt.show()
        
        # Alternative: If you want to auto-close, use plt.show(block=False)
        # but block=True (default) is better for user interaction
    # main execution function
    
    
    
def run(self, target_currency="KES", num_products=10):
        
        """
        Main execution flow - orchestrates all the steps
        
        This is the "master controller" that calls all the other functions
        in the correct order.
        
        Parameters:
            target_currency: Currency code to convert to (default: KES - Kenyan Shilling)
            num_products: Number of products to scrape (default: 10)
            
        Returns:
            True if all steps completed successfully, False otherwise
        """
        print("\n" + "="*70)
        print(" " * 20 + "🏷️  PRICE SCRAPER & CURRENCY CONVERTER  💱")
        print("="*70)
        print(f"Target Currency: {target_currency}")
        print(f"Products to scrape: {num_products}")
        print("="*70)
        
        # ---------- STEP 1: Get Exchange Rates ----------
        # Must happen first because we need rates for conversion
        if not self.get_exchange_rates("GBP"):
            print("[FAILED] Cannot proceed without exchange rates.")
            return False
        
        # ---------- STEP 2: Scrape Products ----------
        if not self.scrape_books(num_products):
            print("[FAILED] Cannot proceed without product data.")
            return False
        
        # ---------- STEP 3: Convert Prices ----------
        if not self.convert_prices(target_currency):
            print("[FAILED] Price conversion failed.")
            return False
        
        # ---------- STEP 4: Display Results ----------
        self.display_table()
        
        # ---------- STEP 5: Save Data ----------
        self.save_to_csv()
        self.save_to_json()
        
        # ---------- STEP 6: Create Visualization ----------
        self.plot_prices()
        
        # ---------- COMPLETION MESSAGE ----------
        print("\n" + "="*70)
        print(" " * 20 + "✅ PROCESS COMPLETED SUCCESSFULLY ✅")
        print("="*70)
        print("Generated files:")
        print("  📄 product_prices.csv - Spreadsheet with all data")
        print("  📄 product_prices.json - JSON format data")
        print("  📄 conversion_metadata.json - Conversion information")
        print("  📊 price_comparison_chart.png - Visualization chart")
        print("="*70)
        
        return True

#interactive mode

def interactive_run():
    """
    Interactive version that asks user for currency and number of products
    
    This provides a more user-friendly experience by showing available
    currencies and letting the user choose.
    """
    # Create a new scraper instance
    scraper = PriceScraperCurrencyConverter()
    
    print("\n" + "="*70)
    print(" " * 15 + "🎮 INTERACTIVE PRICE SCRAPER & CURRENCY CONVERTER 🎮")
    print("="*70)
    
    # First, get exchange rates to show available currencies
    if not scraper.get_exchange_rates("GBP"):
        print("[FAILED] Cannot fetch exchange rates. Please check your internet connection.")
        return
    
    # ---------- CURRENCY SELECTION ----------
    # Define popular currencies to show (prioritize African and major currencies)
    popular_currencies = ['KES', 'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CNY', 'INR', 'NGN', 'ZAR', 'EGP']
    
    # Filter to only show currencies available in the API response
    available_currencies = [c for c in popular_currencies if c in scraper.exchange_rates]
    
    # Also add any other interesting African currencies if available
    african_currencies = ['GHS', 'TZS', 'UGX', 'RWF', 'MAD', 'ETB']
    for currency in african_currencies:
        if currency in scraper.exchange_rates and currency not in available_currencies:
            available_currencies.append(currency)
    
    # Display available currencies with their exchange rates
    print("\n📋 Available Currencies for Conversion:")
    print("─" * 50)
    for i, currency in enumerate(available_currencies, 1):
        rate = scraper.exchange_rates[currency]
        # Special display for popular currencies
        currency_names = {
            'KES': 'Kenyan Shilling', 'USD': 'US Dollar', 'EUR': 'Euro', 
            'GBP': 'British Pound', 'NGN': 'Nigerian Naira', 'ZAR': 'South African Rand'
        }
        name = currency_names.get(currency, '')
        print(f"  {i:2}. {currency}  ({rate:.4f})  {name}")
    print("─" * 50)
    
    # Get user's currency choice
    while True:
        user_input = input(f"\n💱 Select target currency (1-{len(available_currencies)}) or enter currency code: ").strip().upper()
        
        # Check if user entered a number
        if user_input.isdigit() and 1 <= int(user_input) <= len(available_currencies):
            target_currency = available_currencies[int(user_input) - 1]
            break
        # Check if user entered a valid currency code
        elif user_input in scraper.exchange_rates:
            target_currency = user_input
            break
        else:
            print(f"❌ Invalid choice. Please select from {available_currencies} or enter a valid 3-letter currency code.")
    
    # ---------- PRODUCT QUANTITY SELECTION ----------
    while True:
        try:
            # Allow user to enter number, default to 10 if empty
            user_input = input("\n📚 Number of products to scrape (max 50, default 10): ").strip()
            
            if user_input == "":
                num_products = 10
            else:
                num_products = int(user_input)
                # Cap at 50 to avoid rate limiting issues
                num_products = min(num_products, 50)
                
                if num_products <= 0:
                    print("❌ Please enter a positive number.")
                    continue
            break
        except ValueError:
            print("❌ Please enter a valid number.")
    
    # ---------- CONFIRMATION ----------
    print(f"\n✅ Ready to scrape {num_products} books and convert from GBP to {target_currency}")
    confirm = input("\n🚀 Start scraping? (Y/n): ").strip().lower()
    
    if confirm == 'n' or confirm == 'no':
        print("Scraping cancelled.")
        return
    
    # ---------- RUN THE SCRAPER ----------
    scraper.run(target_currency=target_currency, num_products=num_products)
