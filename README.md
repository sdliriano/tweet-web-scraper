# Twitter Web Scraper

A Python-based web scraper that collects tweets from Twitter (X) using Nitter as an alternative frontend. This tool allows you to scrape tweets from any public Twitter account with various filtering options and detailed metadata collection.

## Features

- Scrape tweets from any public Twitter account
- Multiple tweet type filtering options:
  - Original tweets only
  - Original tweets and quote tweets
  - All tweets (including retweets)
- Collects comprehensive tweet metadata:
  - Tweet ID and text content
  - Creation date and time
  - Language detection
  - Engagement metrics (likes, retweets, comments)
  - URLs included in tweets
  - Tweet type classification (original, quote, retweet)
  - Reply status
- Exports data to CSV format
- Handles rate limiting and pagination
- Username hashing for privacy
- Robust error handling and retry mechanisms

## Prerequisites

- Python 3.6 or higher
- Chrome browser installed
- Internet connection

## Installation

1. Clone this repository:
```bash
git clone https://github.com/sdliriano/tweet-web-scraper.git
cd tweet-web-scraper
```

2. Install the required Python packages:
```bash
pip install selenium webdriver-manager langdetect
```

## Usage

1. Run the scraper:
```bash
python scraper.py
```

2. When prompted, enter the tweet type you want to scrape:
   - `original`: Only original tweets
   - `original_and_quotes`: Original tweets and quote tweets
   - `all`: All tweets (including retweets)

3. The script will:
   - Scrape tweets from the specified account
   - Display the results in the console
   - Save the data to a CSV file named `{username}_tweets.csv`

## Output Format

The CSV file contains the following columns:
- `tweet_id`: Unique identifier for the tweet
- `text`: Tweet content
- `created_at`: Tweet creation date and time
- `lang`: Detected language of the tweet
- `user_id_hashed`: Hashed username for privacy
- `retweet_count`: Number of retweets
- `like_count`: Number of likes
- `comment_count`: Number of comments
- `is_reply`: Whether the tweet is a reply
- `is_retweet`: Whether the tweet is a retweet
- `is_quote`: Whether the tweet is a quote tweet
- `urls`: JSON array of URLs included in the tweet

## Notes

- This scraper uses Nitter as an alternative frontend to Twitter to avoid rate limiting and authentication requirements
- The script includes built-in delays and scrolling mechanisms to handle pagination

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and research purposes only. Please ensure you comply with Twitter's terms of service and rate limits when using this scraper. 