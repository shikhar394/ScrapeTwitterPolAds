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
JSON_INDENT = int(config['SPECS']['JSON_INDENT'])

LoginPost = "https://twitter.com/sessions"
URL = "https://twitter.com"
TweetDetailsLink = "https://ads.twitter.com/transparency/line_item_metadata.json?tweet_id=%s&user_id=%s"
TweetOverviewLink = "https://ads.twitter.com/transparency/tweet_performance.json?tweet_id=%s&user_id=%s"
CampaignOverviewLink = "https://ads.twitter.com/transparency/line_item_detail.json?line_item_id=%s"
CampaignDetailsLink = "https://ads.twitter.com/transparency/line_item_targeting_criteria.json?account_id=%s&line_item_id=%s"

data = {"session[username_or_email]": USERNAME,
    "session[password]": PASSWORD,
    "scribe_log": "",
    "redirect_after_login": "/",
    "remember_me": "1"}

Headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}





def GetMetadataForTweets(Tweets, Session):
  """
  Accepts a list of Tweets. Read from Tweets.json in the folder for the particular issue.
  Extracts TweetID and UserID to get tweet performance overview and campaigns tweet was involved
  in. 
  Creates 
    - AllTweets <dict> with TweetIDs as Keys. Every tweetID leads to another dict object. 
        TweetID dicts include TweetPerformance, a list of campaigns tweet was involved in, UserID, ScreenName. 
        Writes to file [ScreenName]/TweetMetadata.json. 
    - CampaingIDs <dict>
        CampaignID = AccountID
        NOTE: CampaignID to AccountID is a many to one relation so far. However, there is a special check in case that changes. 
              See line 96 to 100. 
  Returns 
    - CampaignIDs and ScreenName.
  """
  TweetMetadataList = []
  CampaignIDs = {}
  AllTweets = {}
  UserID = Tweets['UserID']
  ScreenName = Tweets['ScreenName']
  Tweets = Tweets['Tweets']

  for Tweet in Tweets:
    TweetID = Tweet['tweetId']
    AllTweets[TweetID] = {}
    try:
      OverviewTweet = Session.get(TweetOverviewLink % (TweetID, UserID), headers=Headers)
      if OverviewTweet.status_code == 200:
        AllTweets[TweetID]['TweetPerformance'] = json.loads(OverviewTweet.text)
      else:
        SendErrorEmail("Didn't get 200 for tweet overview for " + TweetOverviewLink % (TweetID, UserID))
    except Exception as e:
      SendErrorEmail("Error on " + TweetOverviewLink % (TweetID, UserID) + " Error: " + str(e))
    print(OverviewTweet.text)

    time.sleep(random.randint(MINWAIT/10,MAXWAIT/10))

    try:
      TweetCampaignDetails = Session.get(TweetDetailsLink % (TweetID, UserID), headers=Headers)
      if TweetCampaignDetails.status_code == 200:
        AllTweets[TweetID]['TweetCampaigns'] = json.loads(TweetCampaignDetails.text)
      else:
        SendErrorEmail("Didn't get 200 for tweet overview for " + TweetDetailsLink % (TweetID, UserID))
    except Exception as e:
      SendErrorEmail("Error on " +  TweetDetailsLink % (TweetID, UserID) + " Error: " + str(e))

    for Campaigns in AllTweets[TweetID]['TweetCampaigns']['metadata']:
      if Campaigns['line_item_id'] not in CampaignIDs:
        CampaignIDs[Campaigns['line_item_id']] = Campaigns['account_id']
        print("Campaign IDs" ,CampaignIDs)
      else:
        try: 
          assert(CampaignIDs[Campaigns['line_item_id']] == Campaigns['account_id'])
        except:
          print("AccountID changing for campaigns for " + str(Campaigns) + ScreenName)
          SendErrorEmail("AccountID changing for campaigns for " + str(Campaigns) + ScreenName)
      
    if TweetID in AllTweets:
      if "TweetPerformance" in AllTweets[TweetID] and "TweetCampaigns" in AllTweets[TweetID]:
        AllTweets[TweetID]['ScreenName'] = ScreenName
        AllTweets[TweetID]['UserID'] = UserID

    if len(AllTweets) % 5 == 0:
      WriteToDisk(ScreenName, AllTweets, "TweetMetadata")
  return CampaignIDs, ScreenName, UserID





def CollectCampaignIDs():
  CampaignIDs = {}
  with open("/Users/shikharsakhuja/Desktop/ScrapeTwitterPoliticalAds/crawl_20188910/BetoORourke/TweetMetadata.json") as f:
    Content = json.load(f)
    for Tweet in Content:
      for metadata in Content[Tweet]["TweetCampaigns"]['metadata']:
        CampaignIDs[metadata['line_item_id']] = metadata['account_id']
  return CampaignIDs, 'BetoORourke', "342863309"



def GetMetadataForCampaign(CampaignIDs, ScreenName, UserID, Session):
  """



  """
  Campaign = {}
  pprint(CampaignIDs)

  for CampaignID in CampaignIDs:
    print("Crawling CampaignID: ", CampaignID)
    AccountID = CampaignIDs[CampaignID]
    
    try:
      CampaignOverview = Session.get(CampaignOverviewLink%CampaignID, headers=Headers)
      if CampaignOverview.status_code == 200:
        Campaign[CampaignID] = {}
        Campaign[CampaignID]['Overview'] = json.loads(CampaignOverview.text)
      else:
        SendErrorEmail("Error code not 200 for " + CampaignOverviewLink%CampaignID)
    except Exception as e:
      SendErrorEmail("Error with "+CampaignOverviewLink%CampaignID + ' Error: ' + str(e))

    time.sleep(random.randint(MINWAIT/10,MAXWAIT/10))
    try:
      CampaignTargetingDetails = Session.get(CampaignDetailsLink%(AccountID, CampaignID), headers=Headers)  
      if CampaignTargetingDetails.status_code == 200:
        Campaign[CampaignID]['TargetDetails'] = json.loads(CampaignTargetingDetails.text)
      else:
        SendErrorEmail("Error code not 200 for campaign ID " + CampaignDetailsLink%(AccountID, CampaignID))
    except Exception as e:
      SendErrorEmail("Error with " + CampaignDetailsLink%(AccountID, CampaignID) + ' Error: ' + str(e))

    if CampaignID in Campaign:
      if 'Overview' in Campaign[CampaignID] and 'TargetDetails' in Campaign[CampaignID]:
        Campaign[CampaignID]['ScreenName'] = ScreenName
        Campaign[CampaignID]['UserID'] = UserID

    time.sleep(random.randint(MINWAIT/5, MAXWAIT/5))

    if len(Campaign)%5 == 0:
      WriteToDisk(ScreenName, Campaign, 'CampaignMetadata')






def WriteToDisk(ScreenName, PayloadToWrite, Type):
  print("Writing to ", os.path.join(ScreenName, Type) + '.json')
  File = os.path.join(ScreenName, Type) + '.json'

  with open(File, 'w') as f:
    json.dump(PayloadToWrite, f, indent=JSON_INDENT)

  return





def SendErrorEmail(ErrorMessage):
  msg = MIMEText(str(ErrorMessage))
  msg['from'] = SCRAPEREMAIL
  msg['to'] = ERROREMAIL
  msg['subject'] = 'Error in Metadata script'
  s = smtplib.SMTP('smtp.live.com', 25)
  s.ehlo()
  s.starttls()
  s.login(SCRAPEREMAIL, PASSWORD)
  s.sendmail(SCRAPEREMAIL, [ERROREMAIL], msg.as_string())
  s.quit()





if __name__ == "__main__":
  TwitterAPI = twitter.Twitter(auth=twitter.OAuth(ACCESS_KEY_TOKEN,
    ACCESS_KEY_SECRET, CONSUMER_KEY, CONSUMER_SECRET))
  Start=time.time()
  Path = os.getcwd()
  os.chdir(os.path.join(Path, WriteDir))
  CurrentDirectory = os.getcwd()
  with requests.Session() as Session:
    Resp = Session.get(URL, headers=Headers)
    # get auth token
    soup = BeautifulSoup(Resp.content, "lxml")
    AUTH_TOKEN = soup.select_one("input[name=authenticity_token]")["value"]
    # update data, post and you are logged in.
    data["authenticity_token"] = AUTH_TOKEN
    Resp = Session.post(LoginPost, data=data, headers=Headers)

    UsersWithPoliticalAds = {} #ScreenName:UserID

    for IssueFolder in os.listdir(CurrentDirectory):
      if IssueFolder != 'BetoORourke':
        continue 
      print(IssueFolder)
      TweetFile = os.path.join(CurrentDirectory, IssueFolder, "Tweets.json")
      with open(TweetFile, 'r') as f:
        Tweets = json.load(f)
        #try:
        #CampaignIDs, ScreenName, UserID = GetMetadataForTweets(Tweets, Session)
        #print(Campaigns)
        CampaignIDs, ScreenName, UserID = CollectCampaignIDs()
        GetMetadataForCampaign(CampaignIDs, ScreenName, UserID, Session)
        time.sleep(random.randint(MINWAIT, MAXWAIT))
        #except Exception as e:
        #  SendErrorEmail(e)
        #  continue
  print("Total time to get metadata: ", time.time() - Start)
