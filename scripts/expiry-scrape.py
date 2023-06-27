import requests
import os
import json
import urllib
from bs4 import BeautifulSoup
from datetime import datetime

documentation_site_home = "https://ministryofjustice.github.io/azure-landing-zone-user-guides"

# Get the site home page content
request = requests.get(documentation_site_home)

# Parse the content using BS
soup = BeautifulSoup(request.content, 'html5lib') 

# Setup empty list to store all of the individual article URLs
all_articles = []

# Go through each article in our parsed home page and find all of the links to the individual article pages
# more specifically, find all hrefs that end with "index.html"
for a in soup.find_all('a', href=True):
  if a['href'].endswith("index.html"):
    tidy_url= a['href'].replace("./documentation", "/documentation") # remove the "." from the URL to tidy it up
    all_articles.append(documentation_site_home + tidy_url) # Stick it in the list


# Create a dictionary to store the expiry details for each article (the ones we captured above)
article_expirations = {}

# Go through each of our articles and search for the ""data-module":"page-expiry" element in the html
# Although the name doesn't quite make sense, this seems to contain the date the article will expire on
for article_url in all_articles:
  request = requests.get(article_url)
  soup = BeautifulSoup(request.content, 'html5lib')
  expiry_divs = soup.find_all("div", {"data-module":"page-expiry"})
  for div in expiry_divs:
    review_date = (div['data-last-reviewed-on'])
    article_expirations[article_url] = review_date # store at a Key/value pair: URL/Expiry


expired_articles = {}

# Loop through all the article expiry times and compare to todays date
# Add it to the dictionary if it needs a revision
for article in article_expirations:
   if datetime.strptime(article_expirations[article], '%Y-%m-%d').date() < datetime.today().date():
    expired_articles[article] = article_expirations[article]


multiline_string = ""

for expired in expired_articles :
  document_path = urllib.parse.urlparse(expired).path
  multiline_string += f"Doc: {document_path} - [link]({expired}) - Expired on:  {expired_articles[expired]} \n\n"


# Create the adaptive card
card = {  
  "type": "message",  
  "summary": "ALZ Doc expiry dates",  
  "attachments": [  
    {  
      "contentType": "application/vnd.microsoft.card.adaptive",  
      "contentUrl": "",
      "content": {  
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",  
        "version": "1.3",
        "msteams": { "width": "full" },
        "type": "AdaptiveCard",  
        "body": [  
          {
            "size": "large",
            "style": "Heading",
            "text": "**Expired Documentation - User Guides**",
            "type": "TextBlock",
            "wrap": False
          },
          {  
            "type": "TextBlock",  
            "text": multiline_string,
            "wrap": True
          }  
        ]  
      }  
    }  
  ]  
}

# Serialize the adaptive card to JSON
card_json = json.dumps(card)

# Send the adaptive card to Microsoft Teams
headers = {"Content-Type": "application/json"}

# Get URL from env (mapped by Github action)
webhook_url = os.environ["TEAMS_WEBHOOK_URL"]
response = requests.post(webhook_url, headers=headers, data=card_json)

if response.status_code == 200:
  print("Card sent successfully!")
else:
  print("Error sending card: " + str(response.status_code))