# ScrapeTwitterPoliticalAds

## Code Descriptions

### GetTwitterUserPolads

- Finds all the users with political ads and their information.
- Gets all the tweets for given users, along with the the tweet id and other related info.
- List of potential users to search in congress.csv or TwitterHandles.csv.
- Stores all the screennames of the users as folder names.
- Stores the file as Tweets.json  

### GetTweetsMetadata  

- Crawls all the folders created by GetTwitterUserPolAds.py.
- Uses the tweetIDs to get the metadata of all the ads (spend, impression, etc.). 
- Stores the file as TweetMetadata.json.  

### GetTweetsContents  

- Crawls all the folders created. 
- Uses the tweetIDs to get the ad contents (text, image, etc.).  

## Instructions to run the files

- Install the requirements in a virtualenv.
- Set up a config file with the required information.
- Run the files in the following order:
  - GetTwitterUserPolAds.py
  - GetTweetsMetadata.py
  - GetTweetsContent.py