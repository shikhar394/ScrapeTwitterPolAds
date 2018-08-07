import configparser
import datetime
import json
import os
import random
import smtplib
import sys
import time
import unicodedata
from email.mime.text import MIMEText
from pprint import pprint

import requests
import twitter
from bs4 import BeautifulSoup

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
MAXWAIT = int(config['SPECS']['MAXWAITTWEET'])
MINWAIT = int(config['SPECS']['MINWAITTWEET'])
ERROREMAIL = config['ACCOUNT']['ERROREMAIL']
WriteDir = config['WORKINGDIR']['CURRENT']

LoginPost = "https://twitter.com/sessions"
URL = "https://twitter.com"
TweetsLinkForMetadata = "https://ads.twitter.com/transparency/line_item_metadata.json?tweet_id=%s&user_id=%s"

data = {"session[username_or_email]": USERNAME,
    "session[password]": PASSWORD,
    "scribe_log": "",
    "redirect_after_login": "/",
    "remember_me": "1"}




def GetMetadataForTweets(Tweets, Session):
  TweetMetadataList = []
  UserID = Tweets['UserID']
  ScreenName = Tweets['ScreenName']
  Tweets = Tweets['Tweets']

  for Tweet in Tweets:
    TweetID = Tweet['tweetId']
    TweetMetadata = Session.get(TweetsLinkForMetadata % (TweetID, UserID)).text
    TweetMetadata = json.loads(TweetMetadata)
    TweetMetadata['tweetID'] = TweetID
    TweetMetadata['UserScreenName'] = ScreenName
    TweetMetadata['UserID'] = UserID
    time.sleep(random.randint(MINWAIT/10,MAXWAIT/10))
    TweetMetadataList.append(TweetMetadata)
  WriteToDisk(ScreenName, TweetMetadataList, "Metadata")





def WriteToDisk(ScreenName, PayloadToWrite, Type):
  File = os.path.join(ScreenName, Type) + '.json'

  with open(File, 'w') as f:
    json.dump(PayloadToWrite, f)

  return





if __name__ == "__main__":
  TwitterAPI = twitter.Twitter(auth=twitter.OAuth(ACCESS_KEY_TOKEN,
    ACCESS_KEY_SECRET, CONSUMER_KEY, CONSUMER_SECRET))
  Start=time.time()
  Path = os.getcwd()
  os.chdir(os.path.join(Path, WriteDir))
  CurrentDirectory = os.getcwd()
  with requests.Session() as Session:
    Resp = Session.get(URL)
    # get auth token
    soup = BeautifulSoup(Resp.content, "lxml")
    AUTH_TOKEN = soup.select_one("input[name=authenticity_token]")["value"]
    # update data, post and you are logged in.
    data["authenticity_token"] = AUTH_TOKEN
    Resp = Session.post(LoginPost, data=data)

    UsersWithPoliticalAds = {} #ScreenName:UserID

    for IssueFolder in os.listdir(CurrentDirectory):
      TweetFile = os.path.join(CurrentDirectory, IssueFolder, "Tweets.json")
      with open(TweetFile, 'r') as f:
        Tweets = json.load(f)
        try:
          GetMetadataForTweets(Tweets, Session)
          time.sleep(random.randint(MINWAIT, MAXWAIT))
        except Exception as e:
          msg = MIMEText(str(e))
          msg['from'] = SCRAPEREMAIL
          msg['to'] = ERROREMAIL
          msg['subject'] = 'Error in Metadata script'
          s = smtplib.SMTP('smtp.live.com', 25)
          s.ehlo()
          s.starttls()
          s.login(SCRAPEREMAIL, PASSWORD)
          s.sendmail(SCRAPEREMAIL, [ERROREMAIL], msg.as_string())
          s.quit()
          continue
  print("Total time to get metadata: ", time.time() - Start)
