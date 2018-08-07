import configparser
import datetime
import json
import os
import random
import smtplib
import string
import sys
import time
import unicodedata
from email.mime.text import MIMEText
from pprint import pprint

import requests
import twitter
from bs4 import BeautifulSoup
from requests_oauthlib import OAuth1Session

if len(sys.argv) < 2:
    exit("Usage:python3 FBAdScrapeScript.py crawl_config.cfg")


config = configparser.ConfigParser()
config.read(sys.argv[1])

USERNAME = config['ACCOUNT']['USERNAME']
PASSWORD = config['ACCOUNT']['PASS']
SCRAPEREMAIL = config['ACCOUNT']['EMAIL']
CONSUMER_KEY = config['OAUTH']['CONSUMERKEY']
CONSUMER_SECRET = config['OAUTH']['CONSUMERSECRET']
ACCESS_KEY_TOKEN = config['OAUTH']['TOKENKEY']
ACCESS_KEY_SECRET = config['OAUTH']['TOKENSECRET']
MINWAIT = int(config['SPECS']['MINWAITTWEET'])
MAXWAIT = int(config['SPECS']['MAXWAITTWEET'])
ERROREMAIL = config['ACCOUNT']['ERROREMAIL']
WriteDir = config['WORKINGDIR']['CURRENT']

LoginPost = "https://twitter.com/sessions"
URL = "https://twitter.com"
TweetsLinkForContents = "https://api.twitter.com/1.1/statuses/lookup.json?id=%s"

data = {"session[username_or_email]": USERNAME,
    "session[password]": PASSWORD,
    "scribe_log": "",
    "redirect_after_login": "/",
    "remember_me": "1"}





def GetContentsForTweets(Tweets, Session):
  pprint(Tweets)
  TweetString = ','.join(Tweet['tweetId'] for Tweet in Tweets['Tweets'])
  PayloadToWrite = Session.get(TweetsLinkForContents % (TweetString)).text
  PayloadToWrite = json.loads(PayloadToWrite) #To clean the JSON file
  WriteToDisk(Tweets['ScreenName'], str(PayloadToWrite), "Contents")





def WriteToDisk(ScreenName, PayloadToWrite, Type):
  File = os.path.join(ScreenName, Type) + '.json'
  with open(File, 'w') as f:
    json.dump(PayloadToWrite, f)
  return





if __name__ == "__main__":
  TwitterAPI = twitter.Twitter(auth=twitter.OAuth(ACCESS_KEY_TOKEN,
    ACCESS_KEY_SECRET, CONSUMER_KEY, CONSUMER_SECRET))
  Start = time.time()
  Path = os.getcwd()
  os.chdir(os.path.join(Path, WriteDir))
  CurrentDirectory = os.getcwd()
  TwitterSession = OAuth1Session(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY_TOKEN, ACCESS_KEY_SECRET)
  for IssueFolder in os.listdir(CurrentDirectory):
    TweetFile = os.path.join(CurrentDirectory, IssueFolder, "Tweets.json")
    with open(TweetFile, 'r') as f:
      Tweets = json.load(f)
      try:
        GetContentsForTweets(Tweets, TwitterSession)
        time.sleep(random.randint(MINWAIT,MAXWAIT))
      except Exception as e:
        msg = MIMEText(str(e))
        msg['from'] = SCRAPEREMAIL
        msg['to'] = ERROREMAIL
        msg['subject'] = 'Error in contents script'
        s = smtplib.SMTP('smtp.live.com', 25)
        s.ehlo()
        s.starttls()
        s.sendmail(SCRAPEREMAIL, [ERROREMAIL], msg.as_string())
        s.quit()
  print("Total time to get tweets contents: ", time.time()-Start)
