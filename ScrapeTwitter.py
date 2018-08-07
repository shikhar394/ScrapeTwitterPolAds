import configparser
import csv
import json
import os
import pickle
import shutil
import sys
import time
import urllib.parse
from pprint import pprint
from requests_oauthlib import OAuth1
import oauth2 as oauth

from bs4 import BeautifulSoup
import requests
import twitter
import urllib3

#LINK = "https://ads.twitter.com/transparency/search?q=donald%20trump"

LINK = "https://api.twitter.com/1.1/statuses/lookup.json?cards_platform=Web-12&include_cards=1&include_ext_alt_text=true&include_reply_count=1&tweet_mode=extended&trim_user=0&include_ext_media_color=1&id=1019179087682605056"
    
if __name__ == "__main__":
    # api = {"consumer_key":"nMHVqLcJcbjINxGWnUf8ZlJSu",
    #                 "consumer_secret":"YDX3rigdopqUXaZEbkM9cXvmkZMe4u6k7bwzsicrXNCAUVmdEf",
    #                 "access_token_key":"1019293989760008192-9mbdUiHu08ID8tTjkjcnXfGxoB5TuV",
    #                 "access_token_secret":"VeIKqQsc2yWYUy5qEmMTFltjNt9Dq8MmQhRpN7UFMPdkE"}

    # TwitterAPI = twitter.Twitter(auth=twitter.OAuth("1019293989760008192-9mbdUiHu08ID8tTjkjcnXfGxoB5TuV",
    #         "VeIKqQsc2yWYUy5qEmMTFltjNt9Dq8MmQhRpN7UFMPdkE", "nMHVqLcJcbjINxGWnUf8ZlJSu",
    #         "YDX3rigdopqUXaZEbkM9cXvmkZMe4u6k7bwzsicrXNCAUVmdEf"))

    # pprint(TwitterAPI.users.search(q = '"Beto"'))
        
    # consumer = oauth.Consumer(key=api['consumer_key'], secret=api['consumer_secret'])
    # access_token = oauth.Token(key=api["access_token_key"], secret=api["access_token_secret"])
    # client = oauth.Client(consumer, access_token)

    # timeline_endpoint = LINK
    # response, data = client.request(timeline_endpoint)  
    # with requests.Session() as CurrentSession:
    #   data = {"session[username_or_email]":"shikhar394@gmail.com", "session[password]":"intelcore2duo"}
    #   #data = {"session[username_or_email]":"fbscrape1@outlook.com", "session[password]":"researchproject1"}
    #   post = CurrentSession.post("https://twitter.com/login", data)
    #   print(post.text)
    #   data = CurrentSession.get("https://ads.twitter.com/transparency/tweet_performance.json?tweet_id=1019179087682605056&user_id=342863309")
    #   print(data.text)



    username = "shikhar394"
    password = "intelcore2duo"
    post = "https://twitter.com/sessions"
    url = "https://twitter.com"

    data = {"session[username_or_email]": username,
        "session[password]": password,
        "scribe_log": "",
        "redirect_after_login": "/",
        "remember_me": "1"}

    auth1 = OAuth1("1019293989760008192-9mbdUiHu08ID8tTjkjcnXfGxoB5TuV",
            "VeIKqQsc2yWYUy5qEmMTFltjNt9Dq8MmQhRpN7UFMPdkE", "nMHVqLcJcbjINxGWnUf8ZlJSu",
            "YDX3rigdopqUXaZEbkM9cXvmkZMe4u6k7bwzsicrXNCAUVmdEf")
    print(auth1)
    a = requests.get(LINK, auth=auth1)

    pprint(a.text)

    #with requests.Session() as s:
    #     pprint(s.get("https://ads.twitter.com/transparency/BetoORourke/tweet/1019179087682605056&cards_platform=Web-12&include_cards=1&include_ext_alt_text=true&include_reply_count=1&tweet_mode=extended&trim_user=0&include_ext_media_color=1&id=1019179087682605056").text)
    #     r = s.get(url)
    #     # get auth token
    #     soup = BeautifulSoup(r.content, "lxml")
    #     AUTH_TOKEN = soup.select_one("input[name=authenticity_token]")["value"]
    #     # update data, post and you are logged in.
    #     data["authenticity_token"] = AUTH_TOKEN
    #     r = s.post(post, data=data)
    #     print(r.content)
    #     #print(s.get("https://ads.twitter.com/transparency/tweet_performance.json?tweet_id=1019179087682605056&user_id=342863309").text)
    #     #TODO Find a way to get user IDs
    #     #Get user ID and append it to link to get all tweet IDs
    #     #print(s.get("https://ads.twitter.com/transparency/tweets_timeline.json?user_id=342863309").text)
    #     #Use tweet IDs to append to the link. Gets the metadata of the ads. 
    #     #print(s.get("https://ads.twitter.com/transparency/line_item_metadata.json?tweet_id=1019179087682605056&user_id=342863309").text)
    #     #Find a way to authenticate tweet contents. 




