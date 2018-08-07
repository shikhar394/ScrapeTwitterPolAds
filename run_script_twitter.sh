cd /home/ss9131/TwitterAdScrape

/home/ss9131/TwitterAdScrape/TwitterScrape/bin/python2.7 /home/ss9131/TwitterAdScrape/GetTwitterUserPolAds.py /home/ss9131/TwitterAdScrape/Crawl_config.cfg > TweetsGetScript.out

/home/ss9131/TwitterAdScrape/TwitterScrape/bin/python2.7 /home/ss9131/TwitterAdScrape/GetTweetsMetadata.py /home/ss9131/TwitterAdScrape/Crawl_config.cfg > TweetsMetadataGet.out

/home/ss9131/TwitterAdScrape/TwitterScrape/bin/python2.7 /home/ss9131/TwitterAdScrape/GetTweetsContent.py /home/ss9131/TwitterAdScrape/Crawl_config.cfg > TweetsContentsGet.out
