import threading
import time
import warnings

from TradingInterface import TradingInterface
from TradingStrategy import TradingStrategy
from SentimentAnalysis import SentimentAnalysisSystem

warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
import tweepy
import re
from datetime import datetime

# pretty printing of pandas dataframe
pd.set_option('expand_frame_repr', False)

WRITE_DIR = './twitter_dump'
CRYPTO_LIST = ['SOL']
KEY_FILE = r'./twitter keys.txt'
DB_FILE = r'./all_twitter_data.csv'


class TwitterReader:

    def __init__(self, key_file, db_file):
        self.__secret, self.__key, self.__token = self.read_keys(key_file)
        self.db = pd.read_csv(db_file)

    @staticmethod
    def read_keys(file):
        with open(file) as f:
            secret, key, token = f.read().splitlines()
        return secret, key, token

    # Use tweepy to pull tweets matching query from API
    def get_twitter_v2(self, query, client=None, max_results=10):
        df = pd.DataFrame(columns=["Time", "User", "Followers", "Text"])
        if not client:
            client = tweepy.Client(bearer_token=self.__token,
                                   consumer_key=self.__key,
                                   consumer_secret=self.__secret)

        tweets = client.search_recent_tweets(query, tweet_fields=['created_at'], max_results=max_results)
        for tweet in tweets.data:
            if tweet:
                tweet_object = self.get_tweet(client, tweet.id)
                if 'users' in tweet_object[1].keys():
                    user_object = tweet_object[1]['users'][0].username
                    username = user_object.username
                    follower_count = self.get_followers(client, user_object.id)
                else:
                    username = None
                    follower_count = None
                cleaned_string = clean_string(tweet.text)
                df = pd.concat([df, pd.DataFrame.from_dict({'Time': tweet.data['created_at'],
                                                            "User": username,
                                                            "Followers": follower_count,
                                                            "Text": cleaned_string})], ignore_index=True)

        return df

    # Use Tweepy to pull tweets with given query from Twitter API v1
    # Use to get follower count without separate pull
    def get_twitter_v1(self, query, limit=10):
        auth = tweepy.OAuthHandler(self.__key, self.__secret)
        api = tweepy.API(auth)
        for i in tweepy.Cursor(api.search_tweets,
                               q=query,
                               tweet_mode='extended').items(limit):
            self.db = self.db.append({'Time': i.created_at,
                                      "User": i.user.name,
                                      "Followers": i.user.followers_count,
                                      "Text": clean_string(i.full_text)}, ignore_index=True)

    @staticmethod
    def get_tweet(client, tweet_id):
        tweet = client.get_tweet(tweet_id, expansions=['author_id'], user_fields=['username'])
        return tweet

    @staticmethod
    def get_followers(client, user_id):
        user = client.get_user(id=user_id, user_fields=['public_metrics'])
        return user.data.public_metrics['followers_count']

    def tweets_from_date(self, query, date, limit=1000):
        query = f"{query} until:{date}"
        self.get_twitter_v1(query, limit=limit)

    def write_data(self):
        self.db = self.db[["Time", "User", "Followers", "Text"]]
        self.db["Time"] = pd.to_datetime(self.db["Time"], utc=True)
        self.db = self.db.sort_values(["Time"])
        self.db.to_csv(DB_FILE, index=False)


def clean_string(tweet):
    return re.sub(r'[^a-zA-Z ]', '', tweet)


def read_data():
    reader = TwitterReader(KEY_FILE, DB_FILE)
    search_query = '$SOL OR solana -filter:retweets lang:en'
    reader.tweets_from_date(search_query, '2022-03-15')
    reader.write_data()


if __name__ == '__main__':
    model_path = r"./"
    tokenizer_path = r"./tokenizer.pickle"
    sas = SentimentAnalysisSystem(None, model_path=model_path, tokenizer_path=tokenizer_path)
    window = TradingStrategy(cash=100000, quantity_scaler=1000, analyzer=sas)
    window.start()
    t1 = threading.Thread(target=window.trade, daemon=True)
    t1.start()
    interface = TradingInterface(window)
    time.sleep(600)
    t1.stop()
