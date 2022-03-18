import numpy as np

PRICE_FILE = r"./SOL.csv"
TWEETS_FILE = r"./all_twitter_data.csv"
OUTPUT_FILE = r"./combined_all_data_test.csv"

import pandas as pd
from datetime import timedelta
from datetime import datetime
import os


# INPUTS: 2 CSV files, one with prices and one with tweets
# OUTPUTS: Combined dataframe with tweets and 24 hour price movement & return from time of tweet
def combine_models(price_file, tweets_file):
    prices = pd.read_csv(price_file)
    tweets = pd.read_csv(tweets_file)
    times = pd.to_datetime(tweets["Time"])
    prices['time'] = pd.to_datetime(prices['time'])
    price_list = [lookup_time(t, prices) for t in times]
    tweets["return"] = price_list
    return tweets


# Returns datetime object with the minute following a timestamp
def next_minute(t):
    return t.replace(second=0, microsecond=0, minute=t.minute, hour=t.hour) + timedelta(minutes=1)


# Lookup row in prices database with timestamp matching t
def lookup_time(t, prices):
    time = next_minute(t).strftime("%Y-%m-%d %H:%M")
    row = prices[prices['time'] == time]
    if row.shape[0] == 0:
        return None
    return row['percent'].values[0]


def run_combine_models():
    df = combine_models(PRICE_FILE, TWEETS_FILE)
    df.to_csv(OUTPUT_FILE, index=False)


def combine_files_after(date, filepath):
    files = [filepath+"/"+f for f in os.listdir(filepath)]
    df = None
    for file in files:
        m_time = datetime.fromtimestamp(os.path.getmtime(file))
        if m_time > datetime.strptime(date, "%Y-%m-%d"):
            if df is None:
                df = pd.read_csv(file)
            else:
                df = pd.concat([df,pd.read_csv(file)])
    df.to_csv(filepath+"/all_twitter_data.csv", index=False)

if __name__ == '__main__':
    run_combine_models()

