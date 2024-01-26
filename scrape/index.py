import requests
from bs4 import BeautifulSoup
import datetime
import json
import os

def standardize_date(date_str):
    # Parse the input date string
    parsed_date = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")

    # Format the date in the desired format
    standardized_date = parsed_date.strftime("%d. %B %Y")

    return standardized_date

def call_proxy(url):
    oxy_url = 'https://realtime.oxylabs.io/v1/queries'

    # Define the authentication credentials
    username = 'juliandm'
    password = os.environ.get('OXYLABS_PASSWORD')

    # Define the headers
    headers = {
        'Content-Type': 'application/json',
    }

    # Define the payload data
    payload = {
        'source': 'universal',
        'url': url,
        # 'geo_location': 'United States',
    }
    response = requests.post(oxy_url, auth=(username, password), headers=headers, json=payload)
    if response.status_code != 200:
        print(f"Request failed with status code {response.status_code}")
        print(response.reason)
        return None
    response_json = response.json()
    return response_json["results"][0]["content"]
    # Implement your logic to get a proxy from the 'https://realtime.oxylabs.io/v1/queries' endpoint here
    # Use the provided parameters for authentication and other details


# Function to extract information from a ticker URL
def extract_info_from_ticker(ticker_url):
    txt = call_proxy(ticker_url)

    soup = BeautifulSoup(txt, 'html.parser')
    post_content = soup.find('div', class_='post-content')

    if post_content:
        # Extract post content text
        content_text = post_content.get_text().strip()

        # Extract the source URL
        source_url_element = post_content.find('a', target='_blank', rel='noopener')
        if source_url_element:
            source_url = source_url_element['href'].strip()
        else:
            source_url = None

        return {
            "content": content_text,
            "sourceUrl": source_url
        }
    return None

def create_tweet_summary(post):
    title = post["title"]
    date = post["date"]
    sourceUrl = post.get("sourceUrl", "")
    content = post.get("content", "")

    # if len(content) > 300:
    #     content = content[:97] + "..."
    
    tweet = f"{title}\n{date}\n\n{content}\Quelle: {sourceUrl}"
    return tweet

# Handler function to scrape and return the information
def scrape_info():
    # URL of the page containing the posts
    url = "https://www.afd.de/einzelfallticker/"

    # Send an HTTP GET request to the URL
    txt = call_proxy(url)
    # print(response.reason)
    # Check if the request was successful
    soup = BeautifulSoup(txt, 'html.parser')
    today_date = datetime.datetime.now().strftime("%d. %B %Y")
    posts = []

    article_elements = soup.find_all('article', class_='fusion-post-grid')

    for article in article_elements:
        title = article.find('h2', class_='blog-shortcode-post-title').find('a').text.strip()
        date_element = article.find('span', class_='updated')
        if date_element:
            date_str = date_element.text.strip()
            standardized_date = standardize_date(date_str)
        else:
            standardized_date = article.find('span', string=today_date).text.strip()
        ticker_url = article.find('h2', class_='blog-shortcode-post-title').find('a')['href'].strip()

        if standardized_date == today_date:
            post_info = {
                "title": title,
                "date": standardized_date,
                "tickerUrl": ticker_url
            }
            posts.append(post_info)

    # Create a JSON object to store all the information
    data = {
        "posts": posts
    }

    # Add ticker info to each post
    for post in data["posts"]:
        ticker_info = extract_info_from_ticker(post["tickerUrl"])
        if ticker_info:
            post["content"] = ticker_info["content"]
            post["sourceUrl"] = ticker_info["sourceUrl"]

    # Create tweet summaries for each post
    for post in data["posts"]:
        tweet_summary = create_tweet_summary(post)
        post["summary"] = tweet_summary

    # Return the JSON data
    return json.dumps(data, ensure_ascii=False, indent=2)

def handler(inputs):
    return {
        posts: scrape_info()
    }

# Call the handler function to scrape and return the information
if __name__ == "__main__":
    result = scrape_info()
    print(result)
