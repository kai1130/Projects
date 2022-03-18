import re
import io
import os
import sys
import csv
import time
import math
import random
import tweepy
import datetime
import requests
import numpy as np
import pandas as pd
from collections import deque
from SentimentAnalysis import SentimentAnalysisSystem
from TradingInterface import TradingInterface
import threading


class TradingStrategy:

    def __init__(self, cash, analyzer, quantity_scaler=1, follower_scaler=True):
        self.api_url = r'https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT'
        self.stream = Stream(self)
        self.stream.set_analyzer(analyzer)

        self.quantity_scaler = quantity_scaler
        self.follower_scaler = follower_scaler
        self.initial_cash = cash

        self.small_window = deque()
        self.large_window = deque()
        self.small_window_avg = deque()
        self.large_window_avg = deque()

        self.small_window_size = 10
        self.large_window_size = 20
        self.STRONG_SELL = -2
        self.WEAK_SELL = -1
        self.WEAK_BUY = 1
        self.STRONG_BUY = 2

        self.signal = 0
        self.position = 0
        self.target = 0
        self.cash = cash
        self.holdings = 0
        self.total = cash + self.holdings
        self.pnl = 0

        self.is_on = False
        self.recent_tweets = []
        self.recent_trades = []
        self.new_data = False

    @staticmethod
    def average(lst):
        return sum(lst) / len(lst)

    def print_trade(self, timestamp, type, quantity, price):
        print_string = f'{timestamp} | {type:<5} {quantity:7.3f} SOL @ ${price:5.2f} | Position: {self.position:7.2f} | Holdings: {self.holdings:10,.2f} | Cash: {self.cash:10,.2f}| PnL: {self.pnl:7.2f}'
        self.update_trade_list(print_string)
        print(print_string)

    def on_market_update(self, price_update, disconnect_price=False):
        if disconnect_price is False:
            follower_multiplier = np.sqrt(price_update['followers']) if self.follower_scaler else 1
            self.small_window.append(price_update['sentiment'] * follower_multiplier)
            self.large_window.append(price_update['sentiment'] * follower_multiplier)

            small_window_avg = self.average(self.small_window)
            large_window_avg = self.average(self.large_window)

            self.small_window_avg.append(small_window_avg)
            self.large_window_avg.append(large_window_avg)

            small_window_slope = (self.small_window_avg[-1] - self.small_window_avg[0]) / len(self.small_window)
            large_window_slope = (self.large_window_avg[-1] - self.large_window_avg[0]) / len(self.large_window)

            if len(self.small_window) > self.small_window_size:
                self.small_window.popleft()

            if len(self.large_window) > self.large_window_size:
                self.large_window.popleft()

            if len(self.small_window) == self.small_window_size:

                sentiment_strength = abs(small_window_avg)
                if small_window_avg > 0:
                    if small_window_avg >= large_window_avg:
                        self.signal = self.STRONG_BUY
                    else:
                        self.signal = self.WEAK_BUY
                elif 0 > small_window_avg:
                    if large_window_avg >= small_window_avg:
                        self.signal = self.STRONG_SELL
                    else:
                        self.signal = self.WEAK_SELL
                self.check_signal(price_update, sentiment_strength)
            else:
                pass

        else:
            self.cash += self.position * disconnect_price
            order_size = self.position
            self.position = 0
            self.holdings = self.position * disconnect_price
            self.total = self.holdings + self.cash
            self.pnl = self.total - self.initial_cash
            self.print_trade(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), "Close", order_size,
                             disconnect_price)

    def check_signal(self, price_update, sentiment_strength):
        target_position = self.quantity_scaler * sentiment_strength * self.signal
        self.target = target_position
        order_size = target_position - self.position
        price = price_update['price']
        date = price_update['date']
        action = ''

        if abs(order_size) < .05 * self.quantity_scaler:
            return

        self.position += order_size
        self.cash -= order_size * price
        if order_size > 0:
            action = 'Buy'
        if order_size < 0:
            action = 'Sell'

        self.holdings = self.position * price_update['price']
        self.total = self.holdings + self.cash
        self.pnl = self.total - self.initial_cash

        if action != '':
            self.print_trade(date, action, order_size, price)

    def trade(self):
        self.print_trade(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), "Start", 0,
                         float(requests.get(self.api_url).json()['price']))
        self.is_on = True
        self.stream.filter(track=['$SOL', 'solana'], languages=['en'], threaded=True)

    def start(self):
        self.is_on = True

    def stop(self):
        self.is_on = False
        self.new_data = True
        self.stream.disconnect()

    def update_trade_list(self, trade, max_len=10):
        self.recent_trades.append(trade)
        if len(self.recent_trades) > max_len:
            self.recent_trades = self.recent_trades[1:]

    def update_tweet_list(self, tweet, max_len=10):
        self.new_data = True
        self.recent_tweets.append(tweet)
        if len(self.recent_tweets) > max_len:
            self.recent_tweets = self.recent_tweets[1:]

    def check_new_data(self):
        if self.new_data:
            self.new_data = False
            return True
        return False


class Stream(tweepy.Stream):

    def __init__(self, trading, analyzer=None):

        self.trading = trading
        self.sentiment_model = analyzer

        self.api_url = trading.api_url

        self.consumer_key = 'xxxxx'
        self.consumer_secret = 'xxxxx'
        self.access_token = 'xxxxx'
        self.access_token_secret = 'xxxxx'
        super(self.__class__, self).__init__(self.consumer_key, self.consumer_secret,
                                             self.access_token, self.access_token_secret)

    def set_analyzer(self, sentiment_model):
        self.sentiment_model = sentiment_model

    def generate_sentiment(self, text):
        return self.sentiment_model.predict(text)

    def disconnect(self):
        if self.running is False:
            return
        self.running = False
        self.trading.on_market_update(None, disconnect_price=float(requests.get(self.api_url).json()['price']))

    def on_status(self, status):
        if (not status.retweeted) and ('RT @' not in status.text):
            text = re.sub(r"http\S+", "", re.sub('\s+', ' ', status.text))
            cleaned_text = clean_string(text)
            timestamp = status.created_at
            price = float(requests.get(self.api_url).json()['price'])
            followers = status.user.followers_count
            sentiment = self.generate_sentiment(cleaned_text)

            update = {'date': str(timestamp)[:-6],
                      'symbol': 'SOL',
                      'price': price,
                      'sentiment': sentiment,
                      'followers': followers}
            tweet_string =f"{text} Score: {sentiment:5.3f}"
            print(tweet_string)
            self.trading.update_tweet_list(tweet_string)
            self.trading.on_market_update(update)

def clean_string(tweet):
    return re.sub(r'[^a-zA-Z ]', '', tweet)

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
    window.stop()
