import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime
import time
import matplotlib.pyplot as plt
import re

class PriceScraperCurrencyConverter:
    
    def __init__(self):
        self.base_url = "http://books.toscrape.com"
        self.products_data = []
        self.exchange_rates = {}
        self.conversion_timestamp = None
    
    def get_exchange_rates(self, base_currency="GBP"):
        try:
            url = f"https://open.er-api.com/v6/latest/{base_currency}"
            print(f"\n[INFO] Fetching exchange rates from {base_currency}...")
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("result") == "success":
                self.exchange_rates = data.get("rates", {})
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
            print(f"[ERROR] Network/Request error: {e}")
            return False
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse API response: {e}")
            return False
    
    def clean_price(self, price_text):
        price_match = re.search(r'[\d.]+', price_text)
        if price_match:
            return float(price_match.group())
        return 0.0
    
    def scrape_books(self, num_products=10):
        print(f"\n[INFO] Starting to scrape {num_products} books from {self.base_url}...")
        
        page_num = 1
        products_scraped = 0
        
        while products_scraped < num_products:
            if page_num == 1:
                url = f"{self.base_url}/catalogue/page-1.html"
            else:
                url = f"{self.base_url}/catalogue/page-{page_num}.html"
            
            try:
                print(f"  Accessing page {page_num}...")
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                books = soup.find_all('article', class_='product_pod')
                
                if not books:
                    print(f"  No more books found on page {page_num}")
                    break
                
                for book in books:
                    if products_scraped >= num_products:
                        break
                    
                    title_elem = book.find('h3').find('a')
                    title = title_elem.get('title', title_elem.text.strip())
                    
                    price_elem = book.find('p', class_='price_color')
                    if price_elem:
                        original_price_text = price_elem.text.strip()
                        original_price = self.clean_price(original_price_text)
                    else:
                        original_price_text = "N/A"
                        original_price = 0.0
                    
                    product_info = {
                        'product_name': title,
                        'original_currency': 'GBP',
                        'original_price_text': original_price_text,
                        'original_price_numeric': original_price
                    }
                    
                    self.products_data.append(product_info)
                    products_scraped += 1
                    print(f"    [SCRAPED] {title[:50]}{'...' if len(title) > 50 else ''} - {original_price_text}")
                
                page_num += 1
                time.sleep(0.5)
                
            except requests.exceptions.RequestException as e:
                print(f"  [ERROR] Failed to access page {page_num}: {e}")
                break
            except Exception as e:
                print(f"  [ERROR] Unexpected error parsing page {page_num}: {e}")
                break
        
        print(f"\n[SUCCESS] Scraping complete! Collected {len(self.products_data)} books")
        return len(self.products_data) > 0
    
    def convert_prices(self, target_currency="KES"):
        if not self.exchange_rates:
            print("[ERROR] No exchange rates available. Please fetch rates first.")
            return False
        
        if target_currency not in self.exchange_rates:
            print(f"[ERROR] Currency '{target_currency}' not found in exchange rates")
            print(f"  Available currencies: {list(self.exchange_rates.keys())[:20]}...")
            return False
        
        conversion_rate = self.exchange_rates[target_currency]
        
        print(f"\n[INFO] Converting prices from GBP to {target_currency}")
        print(f"  Exchange rate: 1 GBP = {conversion_rate:.4f} {target_currency}")
        
        for product in self.products_data:
            original_price = product['original_price_numeric']
            converted_price = original_price * conversion_rate
            
            product['target_currency'] = target_currency
            product['converted_price_numeric'] = round(converted_price, 2)
            product['converted_price_text'] = f"{product['target_currency']} {converted_price:.2f}"
            product['exchange_rate_used'] = conversion_rate
        
        print(f"[SUCCESS] Converted {len(self.products_data)} prices to {target_currency}")
        return True
    
    def display_table(self):
        if not self.products_data:
            print("No data to display")
            return
        
        df = pd.DataFrame(self.products_data)
        display_df = df[['product_name', 'original_price_text', 'converted_price_text']].copy()
        display_df.columns = [
            'Product Name', 
            f'Original (GBP)', 
            f'Converted ({df["target_currency"].iloc[0] if len(df) > 0 else "Target"})'
        ]
        
        print("\n" + "="*100)
        print(" " * 35 + "SCRAPED PRODUCTS WITH CONVERTED PRICES")
        print("="*100)
        print(display_df.to_string(index=False))
        print("="*100)
        
        if 'original_price_numeric' in df.columns and 'converted_price_numeric' in df.columns:
            print(f"\nSUMMARY STATISTICS:")
            print(f"  • Total Products Scraped: {len(df)}")
            print(f"  • Original Price Range: {df['original_price_numeric'].min():.2f} - {df['original_price_numeric'].max():.2f} GBP")
            print(f"  • Converted Price Range: {df['converted_price_numeric'].min():.2f} - {df['converted_price_numeric'].max():.2f} {df['target_currency'].iloc[0]}")
            print(f"  • Average Original Price: {df['original_price_numeric'].mean():.2f} GBP")
            print(f"  • Average Converted Price: {df['converted_price_numeric'].mean():.2f} {df['target_currency'].iloc[0]}")
    
    def save_to_csv(self, filename="product_prices.csv"):
        if not self.products_data:
            print("[ERROR] No data to save")
            return False
        
        df = pd.DataFrame(self.products_data)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"\n[SAVED] Data exported to {filename}")
        
        metadata = {
            'conversion_timestamp': self.conversion_timestamp,
            'exchange_rates_used': {
                self.products_data[0]['target_currency']: self.products_data[0]['exchange_rate_used']
            } if self.products_data else {},
            'total_products': len(self.products_data),
            'scrape_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'source_website': self.base_url
        }
        
        with open('conversion_metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"[SAVED] Metadata saved to conversion_metadata.json")
        
        return True
    
    def save_to_json(self, filename="product_prices.json"):
        if not self.products_data:
            print("[ERROR] No data to save")
            return False
        
        output_data = {
            'scrape_info': {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'conversion_timestamp': self.conversion_timestamp,
                'total_products': len(self.products_data),
                'source_url': self.base_url,
                'exchange_rate_source': 'ExchangeRate-API (open.er-api.com)'
            },
            'products': self.products_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"[SAVED] Data exported to {filename}")
        return True
    
    def plot_prices(self):
        if not self.products_data:
            print("[ERROR] No data to plot")
            return
        
        df = pd.DataFrame(self.products_data)
        products_to_plot = min(10, len(df))
        
        product_names = df['product_name'].head(products_to_plot).tolist()
        original_prices = df['original_price_numeric'].head(products_to_plot).tolist()
        converted_prices = df['converted_price_numeric'].head(products_to_plot).tolist()
        
        target_currency = df['target_currency'].iloc[0]
        exchange_rate = df['exchange_rate_used'].iloc[0]
        
        fig, ax = plt.subplots(figsize=(14, 7))
        x = range(len(product_names))
        width = 0.35
        
        bars1 = ax.bar([i - width/2 for i in x], original_prices, width, 
                       label=f'Original (GBP)', color='skyblue', alpha=0.8)
        bars2 = ax.bar([i + width/2 for i in x], converted_prices, width,
                       label=f'Converted ({target_currency})', color='lightcoral', alpha=0.8)
        
        ax.set_title(f' Product Price Comparison: GBP vs {target_currency}\n'
                    f'Exchange Rate: 1 GBP = {exchange_rate:.4f} {target_currency}',
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Product Name', fontsize=11, fontweight='bold')
        ax.set_ylabel('Price', fontsize=11, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(product_names, rotation=45, ha='right', fontsize=9)
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3, axis='y', linestyle='--')
        ax.set_ylim(bottom=0)
        
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}', ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('price_comparison_chart.png', dpi=300, bbox_inches='tight')
        print(f"\n[SAVED] Chart saved as 'price_comparison_chart.png'")
        plt.show()
    
    def run(self, target_currency="KES", num_products=10):
        print("\n" + "="*70)
        print(" " * 20 + "🏷️  PRICE SCRAPER & CURRENCY CONVERTER  💱")
        print("="*70)
        print(f"Target Currency: {target_currency}")
        print(f"Products to scrape: {num_products}")
        print("="*70)
        
        if not self.get_exchange_rates("GBP"):
            print("[FAILED] Cannot proceed without exchange rates.")
            return False
        
        if not self.scrape_books(num_products):
            print("[FAILED] Cannot proceed without product data.")
            return False
        
        if not self.convert_prices(target_currency):
            print("[FAILED] Price conversion failed.")
            return False
        
        self.display_table()
        self.save_to_csv()
        self.save_to_json()
        self.plot_prices()
        
        print("\n" + "="*70)
        print(" " * 20 + "PROCESS COMPLETED SUCCESSFULLY ")
        print("="*70)
        print("Generated files:")
        print("   product_prices.csv - Spreadsheet with all data")
        print("   product_prices.json - JSON format data")
        print("   conversion_metadata.json - Conversion information")
        print("   price_comparison_chart.png - Visualization chart")
        print("="*70)
        
        return True


def interactive_run():
    scraper = PriceScraperCurrencyConverter()
    
    print("\n" + "="*70)
    print(" " * 15 + " INTERACTIVE PRICE SCRAPER & CURRENCY CONVERTER ")
    print("="*70)
    
    if not scraper.get_exchange_rates("GBP"):
        print("[FAILED] Cannot fetch exchange rates. Please check your internet connection.")
        return
    
    popular_currencies = ['KES', 'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CNY', 'INR', 'NGN', 'ZAR', 'EGP']
    available_currencies = [c for c in popular_currencies if c in scraper.exchange_rates]
    
    african_currencies = ['GHS', 'TZS', 'UGX', 'RWF', 'MAD', 'ETB']
    for currency in african_currencies:
        if currency in scraper.exchange_rates and currency not in available_currencies:
            available_currencies.append(currency)
    
    print("\nAvailable Currencies for Conversion:")
    print("─" * 50)
    for i, currency in enumerate(available_currencies, 1):
        rate = scraper.exchange_rates[currency]
        currency_names = {
            'KES': 'Kenyan Shilling', 'USD': 'US Dollar', 'EUR': 'Euro', 
            'GBP': 'British Pound', 'NGN': 'Nigerian Naira', 'ZAR': 'South African Rand'
        }
        name = currency_names.get(currency, '')
        print(f"  {i:2}. {currency}  ({rate:.4f})  {name}")
    print("─" * 50)
    
    while True:
        user_input = input(f"\n Select target currency (1-{len(available_currencies)}) or enter currency code: ").strip().upper()
        
        if user_input.isdigit() and 1 <= int(user_input) <= len(available_currencies):
            target_currency = available_currencies[int(user_input) - 1]
            break
        elif user_input in scraper.exchange_rates:
            target_currency = user_input
            break
        else:
            print(f"Invalid choice. Please select from {available_currencies}")
    
    while True:
        try:
            user_input = input("\n Number of products to scrape (max 50, default 10): ").strip()
            if user_input == "":
                num_products = 10
            else:
                num_products = int(user_input)
                num_products = min(num_products, 50)
                if num_products <= 0:
                    print(" Please enter a positive number.")
                    continue
            break
        except ValueError:
            print(" Please enter a valid number.")
    
    print(f"\n Ready to scrape {num_products} books and convert from GBP to {target_currency}")
    confirm = input("\nStart scraping? (Y/n): ").strip().lower()
    
    if confirm == 'n' or confirm == 'no':
        print("Scraping cancelled.")
        return
    
    scraper.run(target_currency=target_currency, num_products=num_products)


if __name__ == "__main__":
    interactive_run()