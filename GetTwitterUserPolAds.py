import configparser
import csv
import datetime
import json
import os
import random
import shutil
import smtplib
import sys
import time
from email.mime.text import MIMEText
from pprint import pprint

import lxml
import requests
from bs4 import BeautifulSoup
#import oauth2 as oauth
from requests_oauthlib import OAuth1Session
from twitter import *

if len(sys.argv) < 2:
    exit("Usage:python3 FBAdScrapeScript.py crawl_config.cfg [Optional: TwitterHandles.csv]")

TwitterHandlesFile = ''

if len(sys.argv) == 2:
  CrawlFile = sys.argv[1]
  TwitterHandlesFile = 'congress.csv' #Default if a new handles file is not provided. 
  TwitterHandles = False

if len(sys.argv) == 3:
  TwitterHandlesFile = sys.argv[2] # A new twitter handles file is provided. 
  TwitterHandles = True


config = configparser.ConfigParser()
config.read(sys.argv[1])

USERNAME = config['ACCOUNT']['USERNAME']
PASSWORD = config['ACCOUNT']['PASS']
SCRAPEREMAIL = config['ACCOUNT']['EMAIL']
CONSUMER_KEY = config['OAUTH']['CONSUMERKEY']
CONSUMER_SECRET = config['OAUTH']['CONSUMERSECRET']
ACCESS_KEY_TOKEN = config['OAUTH']['TOKENKEY']
ACCESS_KEY_SECRET = config['OAUTH']['TOKENSECRET']
MASTERSEEDLIST = config['SEEDLIST']['MASTERSEEDFILE']
PAGESPERUSER = int(config['SPECS']['PAGES'])
MINWAIT = int(config['SPECS']['MINWAITUSER'])
MAXWAIT = int(config['SPECS']['MAXWAITUSER'])
ERROREMAIL = config['ACCOUNT']['ERROREMAIL']
JSON_INDENT = int(config['SPECS']['JSON_INDENT'])


TwitterAPI = Twitter(auth=OAuth(ACCESS_KEY_TOKEN, ACCESS_KEY_SECRET, 
    CONSUMER_KEY, CONSUMER_SECRET))


LoginPost = "https://twitter.com/sessions"
URL = "https://twitter.com"
PolUserLink = "https://ads.twitter.com/transparency/political_advertisers.json?"
TweetsLinkForUser = "https://ads.twitter.com/transparency/tweets_timeline.json?user_id=%s&cursor=%s"
SearchUserLink = 'https://api.twitter.com/1.1/users/search.json?q=%s&count=20&filter:verified'

data = {"session[username_or_email]": USERNAME,
    "session[password]": PASSWORD,
    "scribe_log": "",
    "redirect_after_login": "/",
    "remember_me": "1"}

now = datetime.datetime.now()
now_str = "".join(str(e) for e in [now.year, now.month, now.day, now.hour])
WriteDir = 'NEWcrawl_'+ now_str # Adding NEW so DB parser doesn't try to parse this until it's complete.

Headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}





def GetUsersWithPoliticalAds(Keyword, Session, TwitterHandles):
  print("Getting tweets for keyword ", Keyword)
  UsersFromKeyword = []
  PayloadToWrite = {}

  if TwitterHandles: # If the twitter handles file, then just make a simple query to get user metadata
    UsersFromKeyword = TwitterAPI.users.search(q=Keyword, include_ext_highlighted_label=True)
  else:
    for i in range(1, PAGESPERUSER+1): # If just keyword search, then make a deep search for all results. 
      TwitterResponse = TwitterAPI.users.search(q=Keyword, count=20, include_ext_highlighted_label=True, page=i)
      UsersFromKeyword.extend(TwitterResponse)
      #print(UsersFromKeyword)
      time.sleep(random.randint(MINWAIT, MAXWAIT))
  count=0
  for User in UsersFromKeyword:
    UserID = User['id_str']
    if User['verified'] or TwitterHandles: #If curated list of twitter handles, don't check for verified stamp
      ScreenName = User['screen_name']
      Tweets = GetTweetsForUser(UserID, ScreenName)
      if Tweets:
        count+=1
        if count>1:
          SendErrorEmail("The annoying user search with mutliple hits " + Keyword)
        PayloadToWrite[User['id_str']] = {}
        PayloadToWrite[User['id_str']]['ScreenName'] = ScreenName
        PayloadToWrite[User['id_str']]['Tweets'] = Tweets

        WriteToDisk(ScreenName, PayloadToWrite, "Tweets")
      time.sleep(random.randint(MINWAIT,MAXWAIT))





def GetTweetsForUser(UserID, ScreenName):
  """
  Gets all the political ads for every user. 
  Works around infinite scrolling through setting the 'cursor' 
  parameter. 
  """
  MoreTweets = True
  Count = 0
  ErrorCount = 0
  AllTweets = []

  while MoreTweets:
    try:
      Tweets = Session.get(TweetsLinkForUser % (UserID, Count), headers=Headers)
      if Tweets.status_code == 200:
        Tweets = json.loads(Tweets.text)["tweets"]
        if len(Tweets):
          AllTweets.extend(Tweets)
          Count += 1
        else:
          MoreTweets = False
      else:
        SendErrorEmail("Not 200 code on " + TweetsLinkForUser % (UserID, Count))
        ErrorCount += 1
        if ErrorCount == 10:
          MoreTweets = False
          SendErrorEmail("Exiting scraping tweets for "+ TweetsLinkForUser % (UserID, Count))
    except Exception as e:
      SendErrorEmail("Error with " + TweetsLinkForUser % (UserID, Count) + " Error: " + str(e))
    time.sleep(random.randint(MINWAIT,MAXWAIT))
  return AllTweets





def WriteToDisk(ScreenName, PayloadToWrite, Type):

  if not os.path.exists(WriteDir):
    os.makedirs(WriteDir)

  if not os.path.exists(os.path.join(WriteDir, ScreenName)):
    os.makedirs(os.path.join(WriteDir, ScreenName))

  UserFolder = os.path.join(WriteDir, ScreenName)
  
  File = os.path.join(UserFolder, Type) + '.json'

  with open(File, 'w') as f:
    json.dump(PayloadToWrite, f, indent=JSON_INDENT)

  return





def extractSeedWordsCSV(FirstName = True, LastName = True):
    """
    Names of Political Candidates in the CSV format. 
    The default parameters allow us to choose whether we want to get first names 
    or last names.
    """
    if TwitterHandlesFile.lower().startswith("twitter"):
      with open(TwitterHandlesFile) as f:
        CurrentSeeds = set([seedWord[2].strip()[len('@'):].lower() for seedWord in csv.reader(f) if seedWord[2].strip()[len('@'):] != ""])
    else:
      with open(TwitterHandlesFile, 'r') as f:
        CurrentSeeds = set([' '.join(seedWord).strip() for seedWord in csv.reader(f) if seedWord != " "])
        CurrentSeeds.update(set([seedWord[1] for seedWord in csv.reader(f) if seedWord != " "]))

    with open(MASTERSEEDLIST, 'w+') as f:
      SeedsMaster = set([Seed.strip() for Seed in f.readlines()])
      for Seed in CurrentSeeds:
        if Seed not in SeedsMaster:
          f.write(Seed + '\n')

    return CurrentSeeds





def AddPolUsersLink(TotalSeeds, Session):
  AllPolUsersFromLink = Session.get(PolUserLink, headers=Headers)
  if AllPolUsersFromLink.status_code == 200:
    AllUsers = json.loads(AllPolUsersFromLink.text)['users']
    for User in AllUsers:
      TotalSeeds.add(User['screenName'].lower())
  else:
    SendErrorEmail("Not 200 code on " + PolUserLink)

  return TotalSeeds





def SendErrorEmail(ErrorMessage):
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
  Start = time.time()
  Count = 0
  UsersWithPol = []
  with requests.Session() as Session:

    Resp = Session.get(URL, headers=Headers)
    # get auth token
    soup = BeautifulSoup(Resp.content, "lxml")
    AUTH_TOKEN = soup.select_one("input[name=authenticity_token]")["value"]
    # update data, post and you are logged in.
    data["authenticity_token"] = AUTH_TOKEN
    Resp = Session.post(LoginPost, data=data, headers=Headers)
    print("Handles file", TwitterHandlesFile)
    TotalSeeds = extractSeedWordsCSV()
    print(len(TotalSeeds))
    TotalSeeds = AddPolUsersLink(TotalSeeds, Session)
    print(len(TotalSeeds))
    #for Keyword in open("Keywords.txt"):
    for Keyword in TotalSeeds:
      Count += 1
      print("Seed # %s out of %s", (Count, len(TotalSeeds)))
      print("Twitter Handles: ", TwitterHandles)
      GetUsersWithPoliticalAds(Keyword.strip(), Session, TwitterHandles)
      time.sleep(random.randint(MINWAIT//10,MAXWAIT//10))
    FinalNameDir = WriteDir[3:]
    shutil.move(WriteDir, FinalNameDir)
    config.set("WORKINGDIR", "CURRENT", FinalNameDir)
    with open(sys.argv[1], 'wb') as configfile:
      config.write(configfile)
    print("Total time to get tweets from users: ", time.time()-Start)
