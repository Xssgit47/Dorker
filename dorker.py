#!/usr/bin/env python3
# Dorker - Google Dork Search Tool (Python Version)

import os
import time
import logging
import random
import json
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))  # Default to 0 if not set

# Rate limiting settings
RATE_LIMIT = 5  # Maximum number of searches per hour
rate_limit_data = {}
rate_limit_file = "rate_limit.json"

# Proxy settings (optional)
USE_PROXIES = False
PROXIES = []  # Add your proxies here in format: ["http://user:pass@ip:port", ...]

# Alternative search engines
SEARCH_ENGINES = [
    {"name": "Google", "url": "https://www.google.com/search?q={query}&num=20"},
    {"name": "Bing", "url": "https://www.bing.com/search?q={query}&count=20"},
    {"name": "DuckDuckGo", "url": "https://duckduckgo.com/html/?q={query}"}
]

def load_rate_limit_data():
    """Load rate limit data from file."""
    global rate_limit_data
    try:
        if os.path.exists(rate_limit_file):
            with open(rate_limit_file, 'r') as f:
                rate_limit_data = json.load(f)
                # Clean up old entries
                now = datetime.now()
                for user_id in list(rate_limit_data.keys()):
                    timestamp = datetime.fromisoformat(rate_limit_data[user_id]["timestamp"])
                    if now - timestamp > timedelta(hours=1):
                        del rate_limit_data[user_id]
    except Exception as e:
        logger.error(f"Error loading rate limit data: {str(e)}")
        rate_limit_data = {}

def save_rate_limit_data():
    """Save rate limit data to file."""
    try:
        with open(rate_limit_file, 'w') as f:
            json.dump(rate_limit_data, f)
    except Exception as e:
        logger.error(f"Error saving rate limit data: {str(e)}")

def check_rate_limit(user_id):
    """Check if user has exceeded rate limit."""
    user_id_str = str(user_id)
    now = datetime.now()
    
    if user_id_str not in rate_limit_data:
        rate_limit_data[user_id_str] = {
            "count": 1,
            "timestamp": now.isoformat()
        }
        save_rate_limit_data()
        return True
    
    user_data = rate_limit_data[user_id_str]
    timestamp = datetime.fromisoformat(user_data["timestamp"])
    
    # Reset if more than an hour has passed
    if now - timestamp > timedelta(hours=1):
        rate_limit_data[user_id_str] = {
            "count": 1,
            "timestamp": now.isoformat()
        }
        save_rate_limit_data()
        return True
    
    # Check if limit exceeded
    if user_data["count"] >= RATE_LIMIT and not is_admin(user_id):
        return False
    
    # Increment count
    user_data["count"] += 1
    save_rate_limit_data()
    return True

def is_admin(user_id):
    """Check if the user is an admin."""
    return user_id == ADMIN_ID

def admin_required(func):
    """Decorator to restrict commands to admin only."""
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        if not is_admin(user_id) and ADMIN_ID != 0:
            update.message.reply_text("Sorry, this command is restricted to admin only.")
            return
        return func(update, context, *args, **kwargs)
    return wrapper

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        'Welcome to Danger Dorker Bot!\n\n'
        'Commands:\n'
        '/dork - Perform a Google dork search\n'
        '/whoami - Show your Telegram ID\n'
        '/status - Show bot status and rate limits\n'
        'Example: /dork intext:password filetype:txt\n\n'
        'For more information about Google dorks, visit: '
        'https://www.exploit-db.com/google-hacking-database'
    )

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text(
        'Danger Dorker Bot Commands:\n\n'
        '/dork [query] - Perform a Google dork search\n'
        '/whoami - Show your Telegram ID\n'
        '/status - Show bot status and rate limits\n'
        '/setadmin [id] - Set a new admin ID (admin only)\n'
        '/engine [name] - Set search engine (Google, Bing, DuckDuckGo)\n\n'
        'Example: /dork intext:password filetype:txt\n\n'
        'Common Google Dork Operators:\n'
        '- intext: - Searches for specific text within pages\n'
        '- intitle: - Searches for specific text in page titles\n'
        '- inurl: - Searches for specific text in URLs\n'
        '- filetype: - Searches for specific file types\n'
        '- site: - Limits searches to specific sites\n'
        '- ext: - Searches for specific file extensions\n\n'
        'Rate Limit: ' + str(RATE_LIMIT) + ' searches per hour (admin unlimited)\n\n'
        'For more information, visit: '
        'https://www.exploit-db.com/google-hacking-database'
    )

def get_random_proxy():
    """Get a random proxy from the list."""
    if not USE_PROXIES or not PROXIES:
        return None
    return random.choice(PROXIES)

def get_search_url(engine_name, query):
    """Get the search URL for the specified engine."""
    engine = next((e for e in SEARCH_ENGINES if e["name"].lower() == engine_name.lower()), SEARCH_ENGINES[0])
    return engine["url"].format(query=requests.utils.quote(query))

def search_with_requests(query: str, engine="Google") -> list:
    """Search using requests library with rotating user agents."""
    try:
        ua = UserAgent()
        headers = {
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/'
        }
        
        url = get_search_url(engine, query)
        
        proxies = {}
        proxy = get_random_proxy()
        if proxy:
            proxies = {
                "http": proxy,
                "https": proxy
            }
        
        response = requests.get(
            url, 
            headers=headers, 
            proxies=proxies if proxies else None,
            timeout=15
        )
        
        if response.status_code != 200:
            logger.error(f"Request failed with status code: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Extract search results based on engine
        if engine.lower() == "google":
            for g in soup.find_all('div', class_='g'):
                anchors = g.find_all('a')
                if anchors:
                    link = anchors[0]['href']
                    title = g.find('h3')
                    if title and link.startswith('http') and 'google.com' not in link:
                        results.append({
                            'title': title.text,
                            'link': link
                        })
        elif engine.lower() == "bing":
            for result in soup.find_all('li', class_='b_algo'):
                link_elem = result.find('a')
                if link_elem and 'href' in link_elem.attrs:
                    link = link_elem['href']
                    title = link_elem.text
                    if link.startswith('http'):
                        results.append({
                            'title': title,
                            'link': link
                        })
        elif engine.lower() == "duckduckgo":
            for result in soup.find_all('div', class_='result'):
                link_elem = result.find('a', class_='result__a')
                if link_elem and 'href' in link_elem.attrs:
                    link = link_elem['href']
                    title = link_elem.text
                    if link.startswith('http'):
                        results.append({
                            'title': title,
                            'link': link
                        })
        
        return results
    except Exception as e:
        logger.error(f"Requests search error: {str(e)}")
        return []

def search_with_selenium(query: str, engine="Google") -> list:
    """Search using Selenium WebDriver."""
    driver = None
    try:
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        # Set random user agent
        ua = UserAgent()
        chrome_options.add_argument(f'user-agent={ua.random}')
        
        # Set proxy if available
        proxy = get_random_proxy()
        if proxy:
            chrome_options.add_argument(f'--proxy-server={proxy}')
        
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Add random delay to mimic human behavior
        time.sleep(random.uniform(1, 3))
        
        # Navigate to search engine
        url = get_search_url(engine, query)
        driver.get(url)
        
        # Wait for results to load
        if engine.lower() == "google":
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.g'))
            )
            
            # Extract results
            results = []
            elements = driver.find_elements(By.CSS_SELECTOR, 'div.g')
            
            for element in elements:
                try:
                    title_element = element.find_element(By.CSS_SELECTOR, 'h3')
                    link_element = element.find_element(By.CSS_SELECTOR, 'a')
                    
                    title = title_element.text
                    link = link_element.get_attribute('href')
                    
                    if link and link.startswith('http') and 'google.com' not in link:
                        results.append({
                            'title': title,
                            'link': link
                        })
                except Exception as e:
                    logger.debug(f"Error extracting result: {str(e)}")
                    continue
            
            return results
        elif engine.lower() == "bing":
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'li.b_algo'))
            )
            
            results = []
            elements = driver.find_elements(By.CSS_SELECTOR, 'li.b_algo')
            
            for element in elements:
                try:
                    link_element = element.find_element(By.CSS_SELECTOR, 'h2 a')
                    title = link_element.text
                    link = link_element.get_attribute('href')
                    
                    if link and link.startswith('http'):
                        results.append({
                            'title': title,
                            'link': link
                        })
                except Exception as e:
                    logger.debug(f"Error extracting Bing result: {str(e)}")
                    continue
            
            return results
        elif engine.lower() == "duckduckgo":
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.result__a'))
            )
            
            results = []
            elements = driver.find_elements(By.CSS_SELECTOR, '.result')
            
            for element in elements:
                try:
                    link_element = element.find_element(By.CSS_SELECTOR, '.result__a')
                    title = link_element.text
                    link = link_element.get_attribute('href')
                    
                    if link and link.startswith('http'):
                        results.append({
                            'title': title,
                            'link': link
                        })
                except Exception as e:
                    logger.debug(f"Error extracting DuckDuckGo result: {str(e)}")
                    continue
            
            return results
    except Exception as e:
        logger.error(f"Selenium search error: {str(e)}")
        return []
    finally:
        if driver:
            driver.quit()

@admin_required
def dork(update: Update, context: CallbackContext) -> None:
    """Handle the /dork command."""
    user_id = update.effective_user.id
    
    # Check rate limit (admins are exempt)
    if not is_admin(user_id) and not check_rate_limit(user_id):
        remaining_time = get_remaining_time(user_id)
        update.message.reply_text(
            f"Rate limit exceeded. You can make {RATE_LIMIT} searches per hour.\n"
            f"Please try again in {remaining_time}."
        )
        return
    
    if not context.args:
        update.message.reply_text('Please provide a dork query. Example: /dork intext:password filetype:txt')
        return
    
    dork_query = ' '.join(context.args)
    
    # Get preferred search engine from user data or default to Google
    engine = context.user_data.get('search_engine', 'Google')
    
    update.message.reply_text(f'Searching for: {dork_query}\nUsing engine: {engine}\nPlease wait...')
    
    # Try multiple search methods to avoid blocking
    results = []
    
    # Method 1: Using requests with custom headers
    try:
        request_results = search_with_requests(dork_query, engine)
        if request_results:
            results = request_results
    except Exception as e:
        logger.error(f"Requests search failed: {str(e)}")
    
    # Method 2: Using Selenium as a last resort
    if not results:
        try:
            update.message.reply_text("First method failed, trying alternative method...")
            selenium_results = search_with_selenium(dork_query, engine)
            if selenium_results:
                results = selenium_results
        except Exception as e:
            logger.error(f"Selenium search failed: {str(e)}")
    
    # Send results
    if results:
        # Format and send results
        message = f"Results for: {dork_query}\nEngine: {engine}\n\n"
        
        # Limit to 10 results to avoid message length issues
        limited_results = results[:10]
        
        for i, result in enumerate(limited_results, 1):
            message += f"{i}. {result['title']}\n{result['link']}\n\n"
        
        if len(results) > 10:
            message += f"\nShowing 10 of {len(results)} results."
        
        update.message.reply_text(message)
    else:
        # Try another search engine if the first one failed
        if engine.lower() == "google":
            alt_engine = "Bing"
        elif engine.lower() == "bing":
            alt_engine = "DuckDuckGo"
        else:
            alt_engine = "Google"
            
        update.message.reply_text(
            f"No results found for: {dork_query} using {engine}.\n"
            f"The search engine might be blocking the request.\n"
            f"Try using a different search engine with: /engine {alt_engine}"
        )

def set_admin(update: Update, context: CallbackContext) -> None:
    """Set the admin ID."""
    # Only allow setting admin if no admin is set yet or if the current user is admin
    
    global ADMIN_ID  # Move this to the top before using ADMIN_ID

    # Only allow setting admin if no admin is set yet or if the current user is admin
    user_id = update.effective_user.id

    if ADMIN_ID == 0 or is_admin(user_id):  # ADMIN_ID is used here
        if not context.args:
            update.message.reply_text("Please provide a user ID. Example: /setadmin 123456789")
            return

        try:
            new_admin_id = int(context.args[0])
            update.message.reply_text(
                f"Admin ID set to {new_admin_id} for this session.\n\n"
                f"To make this permanent, please update your .env file with:\n"
                f"ADMIN_ID={new_admin_id}"
            )
            
            # Now assigning the new value
            ADMIN_ID = new_admin_id

        except ValueError:
            update.message.reply_text("Invalid user ID. Please provide a numeric ID.")

    else:
        update.message.reply_text("Only the current admin can change the admin ID.")

def whoami(update: Update, context: CallbackContext) -> None:
    """Tell the user their ID."""
    user_id = update.effective_user.id
    is_admin_user = is_admin(user_id)
    admin_status = "You are the admin of this bot." if is_admin_user else "You are not an admin of this bot."
    
    update.message.reply_text(
        f"Your Telegram ID is: {user_id}\n{admin_status}"
    )

def set_engine(update: Update, context: CallbackContext) -> None:
    """Set the preferred search engine."""
    if not context.args:
        update.message.reply_text(
            "Please specify a search engine. Available options:\n"
            "- Google\n"
            "- Bing\n"
            "- DuckDuckGo\n\n"
            "Example: /engine Bing"
        )
        return
    
    engine = context.args[0].capitalize()
    valid_engines = ["Google", "Bing", "DuckDuckGo"]
    
    if engine not in valid_engines:
        update.message.reply_text(
            f"Invalid search engine. Available options: {', '.join(valid_engines)}"
        )
        return
    
    # Store the preferred engine in user data
    if not context.user_data:
        context.user_data = {}
    context.user_data['search_engine'] = engine
    
    update.message.reply_text(f"Search engine set to: {engine}")

def get_remaining_time(user_id):
    """Get the remaining time until rate limit reset."""
    user_id_str = str(user_id)
    if user_id_str not in rate_limit_data:
        return "0 minutes"
    
    user_data = rate_limit_data[user_id_str]
    timestamp = datetime.fromisoformat(user_data["timestamp"])
    now = datetime.now()
    
    # Calculate time until reset (1 hour from the first request)
    reset_time = timestamp + timedelta(hours=1)
    remaining = reset_time - now
    
    if remaining.total_seconds() <= 0:
        return "0 minutes"
    
    minutes = int(remaining.total_seconds() / 60)
    return f"{minutes} minutes"

def status(update: Update, context: CallbackContext) -> None:
    """Show bot status and rate limits."""
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    
    is_admin_user = is_admin(user_id)
    admin_status = "You are the admin of this bot." if is_admin_user else "You are not an admin of this bot."
    
    # Get rate limit info
    searches_used = 0
    remaining = RATE_LIMIT
    time_remaining = "N/A"
    
    if user_id_str in rate_limit_data:
        user_data = rate_limit_data[user_id_str]
        searches_used = user_data["count"]
        remaining = max(0, RATE_LIMIT - searches_used)
        time_remaining = get_remaining_time(user_id)
    
    # Get preferred search engine
    engine = context.user_data.get('search_engine', 'Google') if context.user_data else 'Google'
    
    update.message.reply_text(
        f"Bot Status:\n\n"
        f"Your ID: {user_id}\n"
        f"{admin_status}\n\n"
        f"Rate Limit: {RATE_LIMIT} searches per hour\n"
        f"Searches used: {searches_used}\n"
        f"Searches remaining: {remaining if not is_admin_user else 'Unlimited'}\n"
        f"Time until reset: {time_remaining if not is_admin_user else 'N/A'}\n\n"
        f"Current search engine: {engine}"
    )

def main() -> None:
    """Start the bot."""
    # Load rate limit data
    load_rate_limit_data()
    
    # Create the Updater and pass it your bot's token
    updater = Updater(TELEGRAM_BOT_TOKEN)
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("dork", dork))
    dispatcher.add_handler(CommandHandler("setadmin", set_admin))
    dispatcher.add_handler(CommandHandler("whoami", whoami))
    dispatcher.add_handler(CommandHandler("engine", set_engine))
    dispatcher.add_handler(CommandHandler("status", status))
    
    # Start the Bot
    updater.start_polling()
    logger.info("Dorker bot is running...")
    
    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
