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
JSON_INDENT = int(config['SPECS']['JSON_INDENT'])


LoginPost = "https://twitter.com/sessions"
URL = "https://twitter.com"
TweetsLinkForContents = "https://api.twitter.com/1.1/statuses/lookup.json?id=%s&include_ext_alt_text=true&include_card_uri=true"

data = {"session[username_or_email]": USERNAME,
    "session[password]": PASSWORD,
    "scribe_log": "",
    "redirect_after_login": "/",
    "remember_me": "1"}





def GetContentsForTweets(Tweets, Session):
  TempTweetList = []
  AllTweets = []
  AllTweetLength = len(Tweets['Tweets'])
  for Tweet in Tweets['Tweets']:
    
    TempTweetList.append(Tweet['tweetId'])
    
    if len(TempTweetList) == 100:
      TweetString = ','.join(TweetID for TweetID in TempTweetList)
      AllTweets.extend(GetContentForTweetString(TweetString, Session))
      TempTweetList = []
      time.sleep(random.randint(MINWAIT, MAXWAIT))
  TweetString = ','.join(TweetID for TweetID in TempTweetList)
  AllTweets.extend(GetContentForTweetString(TweetString, Session))
  WriteToDisk(Tweets['ScreenName'], AllTweets, 'TweetContents')






def GetContentForTweetString(TweetString, Session):
  try:
    TweetChunk = Session.get(TweetsLinkForContents % (TweetString))
    if TweetChunk.status_code == 200:
      TweetChunk = json.loads(TweetChunk.text)
    else:
      SendErrorEmail("Status code not 200 for " + TweetsLinkForContents % (TweetString))
  except Exception as e:
    SendErrorEmail("Error : " + str(e) + " on " +  TweetsLinkForContents % (TweetString))
  print(TweetChunk, type(TweetChunk))
  return TweetChunk





def WriteToDisk(ScreenName, PayloadToWrite, Type):
  File = os.path.join(ScreenName, Type) + '.json'
  with open(File, 'w') as f:
    json.dump(PayloadToWrite, f, indent=JSON_INDENT)
  return





def SendErrorEmail(ErrorMessage):
  print(ErrorMessage)
  msg = MIMEText(str(ErrorMessage))
  msg['from'] = SCRAPEREMAIL
  msg['to'] = ERROREMAIL
  msg['subject'] = 'Error in getting tweets script'
  s = smtplib.SMTP('smtp.live.com', 25)
  s.ehlo()
  s.starttls()
  s.login(SCRAPEREMAIL, PASSWORD)
  s.sendmail(SCRAPEREMAIL, [ERROREMAIL], msg.as_string())
  s.quit()





if __name__ == "__main__":
  TwitterAPI = twitter.Twitter(auth=twitter.OAuth(ACCESS_KEY_TOKEN,
    ACCESS_KEY_SECRET, CONSUMER_KEY, CONSUMER_SECRET))
  Start = time.time()
  Path = os.getcwd()
  os.chdir(os.path.join(Path, WriteDir))
  CurrentDirectory = os.getcwd()
  TwitterSession = OAuth1Session(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY_TOKEN, ACCESS_KEY_SECRET)
  for IssueFolder in os.listdir(CurrentDirectory):
    if IssueFolder[0] == '.': #Ignore hidden files.
      continue
    TweetFile = os.path.join(CurrentDirectory, IssueFolder, "Tweets.json")
    with open(TweetFile, 'r') as f:
      Tweets = json.load(f)
      try:
        GetContentsForTweets(Tweets, TwitterSession)
        time.sleep(random.randint(MINWAIT,MAXWAIT))
      except Exception as e:
        SendErrorEmail(e)
  print("Total time to get tweets contents: ", time.time()-Start)
