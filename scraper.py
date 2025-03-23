from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import csv
import json
from datetime import datetime, timedelta
import re
import hashlib
from langdetect import detect

def hash_username(username):
    """Create a consistent hash for a username."""
    return hashlib.sha256(username.encode()).hexdigest()[:16]

def detect_language(text):
    """Detect the language of the text, defaulting to 'en' if uncertain."""
    try:
        return detect(text)
    except:
        return 'en'

def parse_date(date_str):
    """Parse Nitter date format into datetime object."""
    try:
        # Handle the title attribute format (e.g. "Mar 23, 2025 · 5:15 PM UTC")
        if '·' in date_str:
            # Split the date and time parts
            date_part = date_str.split('·')[0].strip()
            time_part = date_str.split('·')[1].strip().replace(' UTC', '')
            # Combine them and parse
            full_datetime_str = f"{date_part} {time_part}"
            return datetime.strptime(full_datetime_str, '%b %d, %Y %I:%M %p')
            
        now = datetime.now()
        
        if 'ago' in date_str:
            # Handle relative times
            if 'h ago' in date_str:
                hours = int(date_str.split('h')[0])
                return now - timedelta(hours=hours)
            elif 'm ago' in date_str:
                minutes = int(date_str.split('m')[0])
                return now - timedelta(minutes=minutes)
            elif 'd ago' in date_str:
                days = int(date_str.split('d')[0])
                return now - timedelta(days=days)
        else:
            # Handle absolute dates
            if ',' in date_str:  # Format: "Dec 25, 2023"
                return datetime.strptime(date_str, '%b %d, %Y')
            else:  # Format: "Dec 25"
                date = datetime.strptime(date_str, '%b %d')
                # If the parsed date is in the future, use last year
                result = date.replace(year=now.year)
                if result > now:
                    result = result.replace(year=now.year - 1)
                return result
    except:
        return now  # Return current time if parsing fails

def extract_tweet_id(url):
    """Extract tweet ID from the Nitter URL."""
    try:
        match = re.search(r'/status/(\d+)', url)
        return match.group(1) if match else None
    except:
        return None

def extract_urls(tweet_element):
    """Extract URLs from tweet."""
    try:
        urls = []
        link_elements = tweet_element.find_elements(By.CSS_SELECTOR, '.tweet-content a')
        for link in link_elements:
            url = link.get_attribute('href')
            if url and not url.startswith('/'):  # Exclude internal Nitter links
                urls.append(url)
        return urls
    except:
        return []

def is_retweet(container):
    """Check if the tweet is a retweet."""
    try:
        retweet_header = container.find_elements(By.CSS_SELECTOR, '.retweet-header')
        return len(retweet_header) > 0
    except:
        return False

def is_quote_tweet(container):
    """Check if the tweet is a quote tweet."""
    try:
        quote_container = container.find_elements(By.CSS_SELECTOR, '.quote')
        return len(quote_container) > 0
    except:
        return False

def extract_engagement_stats(container):
    """Extract retweet, like, and comment counts using CSS selectors."""
    try:
        stats = {'retweet_count': 0, 'like_count': 0, 'comment_count': 0}
        
        # Use CSS selectors that match the actual HTML structure
        def parse_count(element):
            try:
                if element:
                    text = element.text.strip()
                    # Convert abbreviated numbers (e.g., "1.2K" to 1200)
                    text = text.lower().strip()
                    if 'k' in text:
                        return int(float(text.replace('k', '')) * 1000)
                    elif 'm' in text:
                        return int(float(text.replace('m', '')) * 1000000)
                    # Remove any non-digit characters and convert to int
                    return int(''.join(filter(str.isdigit, text))) if text else 0
                return 0
            except:
                return 0
        
        # Extract each stat using CSS selectors
        try:
            comment_element = container.find_element(By.CSS_SELECTOR, '.icon-comment').find_element(By.XPATH, '..')
            stats['comment_count'] = parse_count(comment_element)
        except Exception as e:
            print(f"Error extracting comment count: {str(e)}")
            
        try:
            retweet_element = container.find_element(By.CSS_SELECTOR, '.icon-retweet').find_element(By.XPATH, '..')
            stats['retweet_count'] = parse_count(retweet_element)
        except Exception as e:
            print(f"Error extracting retweet count: {str(e)}")
            
        try:
            like_element = container.find_element(By.CSS_SELECTOR, '.icon-heart').find_element(By.XPATH, '..')
            stats['like_count'] = parse_count(like_element)
        except Exception as e:
            print(f"Error extracting like count: {str(e)}")
                
        return stats
    except Exception as e:
        print(f"Error extracting engagement stats: {str(e)}")
        return {'retweet_count': 0, 'like_count': 0, 'comment_count': 0}

def scrape_x_posts(username, num_scrolls=5, tweet_type='original'):
    """Scrapes posts from Nitter with enhanced data collection.
    
    Args:
        username (str): The Twitter username to scrape
        num_scrolls (int): Number of times to scroll/load more tweets
        tweet_type (str): Type of tweets to include:
            'original' - Only original tweets
            'original_and_quotes' - Original tweets and quote tweets
            'all' - All tweets (original, quotes, and retweets)
    """
    
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Commented out for debugging
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)
    
    try:
        url = f"https://nitter.net/{username}"
        driver.get(url)
        time.sleep(5)  # Initial load
        
        posts = []
        scroll_count = 0
        user_id_hashed = hash_username(username)
        seen_ids = set()  # Track seen tweet IDs
        
        while scroll_count < num_scrolls:
            try:
                tweet_containers = wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.timeline-item'))
                )

                for container in tweet_containers:
                    try:
                        # Check tweet type and filter accordingly
                        is_rt = is_retweet(container)
                        is_quote = is_quote_tweet(container)
                        
                        # Skip based on tweet_type setting
                        if tweet_type == 'original' and (is_rt or is_quote):
                            continue
                        elif tweet_type == 'original_and_quotes' and is_rt:
                            continue
                        # For 'all', we don't skip any tweets
                            
                        # Get tweet URL and ID first to check for duplicates
                        date_element = container.find_element(By.CSS_SELECTOR, '.tweet-date a')
                        tweet_url = date_element.get_attribute('href')
                        tweet_id = extract_tweet_id(tweet_url)
                        
                        # Skip if we've seen this tweet before
                        if not tweet_id or tweet_id in seen_ids:
                            continue
                        
                        seen_ids.add(tweet_id)
                            
                        # Basic tweet content
                        tweet_element = container.find_element(By.CSS_SELECTOR, '.tweet-content')
                        tweet_text = tweet_element.text.strip()
                        
                        # Use the title attribute for the date instead of the text content
                        date_text = date_element.get_attribute('title')
                        parsed_date = parse_date(date_text)
                        
                        # Get engagement metrics using the new function
                        stats = extract_engagement_stats(container)
                        
                        # Check if it's a reply
                        is_reply = bool(container.find_elements(By.CSS_SELECTOR, '.replying-to'))
                        
                        # Extract URLs
                        urls = extract_urls(tweet_element)
                        
                        # Create enhanced tweet object
                        tweet_data = {
                            'tweet_id': tweet_id,
                            'text': tweet_text,
                            'created_at': parsed_date.strftime('%Y-%m-%d %H:%M:%S'),
                            'lang': detect_language(tweet_text),
                            'user_id_hashed': user_id_hashed,
                            'retweet_count': stats['retweet_count'],
                            'like_count': stats['like_count'],
                            'comment_count': stats['comment_count'],
                            'is_reply': is_reply,
                            'is_retweet': is_rt,
                            'is_quote': is_quote,
                            'urls': urls
                        }
                        
                        posts.append(tweet_data)
                            
                    except Exception as e:
                        continue
                
                try:
                    load_more = driver.find_element(By.XPATH, "//a[contains(text(), 'Load more')]")
                    driver.execute_script("arguments[0].scrollIntoView();", load_more)
                    time.sleep(1)
                    load_more.click()
                    time.sleep(3)
                    scroll_count += 1
                except Exception as e:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    scroll_count += 1

            except Exception as e:
                print(f"Error while scrolling: {str(e)}")
                scroll_count += 1
                continue

        # Sort posts by date
        posts.sort(key=lambda x: datetime.strptime(x['created_at'], '%Y-%m-%d %H:%M:%S'), reverse=True)
        return posts

    finally:
        driver.quit()

def export_to_csv(tweets, username):
    """Export tweets to a CSV file with enhanced schema."""
    filename = f"{username}_tweets.csv"
    fieldnames = ['tweet_id', 'text', 'created_at', 'lang', 'user_id_hashed', 
                 'retweet_count', 'like_count', 'comment_count', 'is_reply',
                 'is_retweet', 'is_quote', 'urls']
    
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for tweet in tweets:
            # Convert URLs list to string to fit in CSV
            tweet_row = tweet.copy()
            tweet_row['urls'] = json.dumps(tweet_row['urls'])
            writer.writerow(tweet_row)
    return filename

# Example Usage
if __name__ == "__main__":
    user = "elonmusk"
    tweet_type = input("Enter tweet type to scrape ('original', 'original_and_quotes', or 'all'): ").strip()
    if tweet_type not in ['original', 'original_and_quotes', 'all']:
        print("Invalid tweet type. Defaulting to 'original'")
        tweet_type = 'original'
    
    tweets = scrape_x_posts(user, num_scrolls=20, tweet_type=tweet_type)
    
    # Print to console
    print(f"\nScraped {len(tweets)} tweets from @{user}:")
    for i, tweet in enumerate(tweets, 1):
        tweet_type_str = "RETWEET" if tweet['is_retweet'] else "QUOTE" if tweet['is_quote'] else "TWEET"
        print(f"\n{i}. [{tweet_type_str}] [ID: {tweet['tweet_id']}] [{tweet['created_at']}] [{tweet['lang']}]")
        print(f"   Text: {tweet['text']}")
        print(f"   Engagement: {tweet['comment_count']} comments, {tweet['retweet_count']} RTs, {tweet['like_count']} likes")
        if tweet['urls']:
            print(f"   URLs: {', '.join(tweet['urls'])}")
    
    # Export to CSV
    csv_file = export_to_csv(tweets, user)
    print(f"\nTweets exported to {csv_file}")
