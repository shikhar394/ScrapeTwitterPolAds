import configparser
import csv
import datetime
import json
import os
import random
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
MASTERSEEDLIST = config['SEEDLIST']['MASTERSEEDFILE']
PAGESPERUSER = int(config['SPECS']['PAGES'])
MINWAIT = int(config['SPECS']['MINWAITUSER'])
MAXWAIT = int(config['SPECS']['MAXWAITUSER'])
ERROREMAIL = config['ACCOUNT']['ERROREMAIL']

TwitterAPI = Twitter(auth=OAuth(ACCESS_KEY_TOKEN, ACCESS_KEY_SECRET, 
    CONSUMER_KEY, CONSUMER_SECRET))


LoginPost = "https://twitter.com/sessions"
URL = "https://twitter.com"
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





def GetUsersWithPoliticalAds(Keyword, Session):
  print("Getting tweets for keyword ", Keyword)
  #UsersFromKeyword = TwitterAPI.users.search(q = Keyword, count = 50)
  #UsersFromKeyword = TwitterAPI.users.search(q = Keyword.strip(), count = 50, 
  #    include_ext_highlighted_label=True)
  UsersFromKeyword = []
  for i in range(1, PAGESPERUSER+1):
    UsersFromKeyword.extend(TwitterAPI.users.search(q=Keyword, count=20, include_ext_highlighted_label=True, page=i))
    time.sleep(random.randint(MINWAIT, MAXWAIT))

  
    for User in UsersFromKeyword:
      print(User['verified'])
      print("At user ", User['screen_name'])
      print(type(User))
      print(User['ext_highlighted_label'])
      if User['verified']:
        UserID = User['id_str']
        ScreenName = User['screen_name']
        Tweets = GetTweetsForUser(UserID, ScreenName)
        

        PayloadToWrite = {}
        PayloadToWrite['UserID'] = User['id_str']
        PayloadToWrite['ScreenName'] = ScreenName
        PayloadToWrite['Tweets'] = Tweets

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
  AllTweets = []
  with open(WriteDir[3:]+"ErrorLog.txt", 'a+') as f:
    while MoreTweets:
      Tweets = Session.get(TweetsLinkForUser % (UserID, Count)).text
      try:
        Tweets = json.loads(Tweets)["tweets"]
        if len(Tweets):
          AllTweets.extend(Tweets)
          Count += 1
        else:
          MoreTweets = False
      except:
        f.write(ScreenName + '\n' + str(Tweets) + '\n')
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
    json.dump(PayloadToWrite, f)

  return





def extractSeedWordsCSV(SeedListName, FirstName = True, LastName = True):
    """
    Names of Political Candidates in the CSV format. 
    The default parameters allow us to choose whether we want to get first names 
    or last names.
    """
    with open(SeedListName, 'r') as f:
      CurrentSeeds = set([' '.join(seedWord).strip() for seedWord in csv.reader(f) if seedWord != " "])
      CurrentSeeds.update(set([seedWord[1] for seedWord in csv.reader(f) if seedWord != " "]))

    with open(MASTERSEEDLIST, 'w+') as f:
      SeedsMaster = set([Seed.strip() for Seed in f.readlines()])
      for Seed in CurrentSeeds:
        if Seed not in SeedsMaster:
          f.write(Seed + '\n')

    return CurrentSeeds





if __name__ == "__main__":
  Start = time.time()
  Count = 0
  UsersWithPol = []
  with requests.Session() as Session:
    Resp = Session.get(URL)
    # get auth token
    soup = BeautifulSoup(Resp.content, "lxml")
    AUTH_TOKEN = soup.select_one("input[name=authenticity_token]")["value"]
    # update data, post and you are logged in.
    data["authenticity_token"] = AUTH_TOKEN
    Resp = Session.post(LoginPost, data=data)
    TotalSeeds = extractSeedWordsCSV("congress.csv")
    #for Keyword in open("Keywords.txt"):
    for Keyword in TotalSeeds:
      print("Seed # %s out of %s", (Count, len(TotalSeeds)))
      try:
        GetUsersWithPoliticalAds(Keyword.strip(), Session)
        time.sleep(random.randint(MINWAIT,MAXWAIT))
      except Exception as e:
        msg = MIMEText(str(e))
        msg['from'] = SCRAPEREMAIL
        msg['to'] = ERROREMAIL
        msg['subject'] = 'Error in ads script'
        s = smtplib.SMTP('smtp.live.com', 25)
        s.ehlo()
        s.starttls()
        s.login(SCRAPEREMAIL, PASSWORD)
        s.sendmail(SCRAPEREMAIL, [ERROREMAIL], msg.as_string())
        s.quit()
    FinalNameDir = WriteDir[3:]
    os.rename(WriteDir, FinalNameDir)
    config.set("WORKINGDIR", "CURRENT", FinalNameDir)
    with open(sys.argv[1], 'wb') as configfile:
      config.write(configfile)
    print("Total time to get tweets from users: ", time.time()-Start)
