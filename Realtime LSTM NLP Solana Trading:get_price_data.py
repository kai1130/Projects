import time
import pandas as pd
import requests
from main import CRYPTO_LIST
import numpy as np
import datetime as dt

WRITE_DIR = './crypto_prices'


class CryptoPriceReader:

    def __init__(self, file):
        self.db = pd.read_csv(file)

    @staticmethod
    def get_current_data(from_sym, to_sym='USD', exchange=''):
        url = 'https://min-api.cryptocompare.com/data/price'

        parameters = {'fsym': from_sym,
                      'tsyms': to_sym}

        if exchange:
            parameters['e'] = exchange

        # response comes as json
        response = requests.get(url, params=parameters)
        data = response.json()

        return data

    def get_historical_data(self, from_sym, to_sym='USD', exchange='', freq='minute', limit=1440, end_date=None):
        url = 'https://min-api.cryptocompare.com/data/v2/histo'
        url += freq

        parameters = {'fsym': from_sym,
                      'tsym': to_sym,
                      'limit': limit}
        if end_date:
            parameters['toTs'] = end_date

        if exchange:
            print('exchange: ', exchange)
            parameters['e'] = exchange

        response = requests.get(url, params=parameters)
        data = response.json()
        df = pd.DataFrame.from_dict(data['Data']['Data'])
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df.drop(['conversionType', 'conversionSymbol'], axis=1)
        self.db = pd.concat([self.db, df])

    def add_returns(self, freq='minute'):
        time_dict = {'day': 1, 'hour': 24, 'minute': 1440}
        window = time_dict[freq]
        self.db['time'] = pd.to_datetime(self.db['time'], utc=True)
        self.db = self.db.sort_values(['time'])
        self.db = self.db.drop_duplicates(subset=['time'])
        self.db['move'] = np.append(self.db['close'].diff(window)[window:].values, [None] * window)
        self.db['percent'] = self.db['move'] / self.db['close']

    def write_db(self, path):
        self.db.to_csv(path, index=False)

if __name__ == '__main__':
    dates = [time.mktime((dt.datetime.now() - dt.timedelta(days=i)).timetuple()) for i in range(0,2)]
    for symbol in CRYPTO_LIST:
        price_file = f"{WRITE_DIR}/{symbol}.csv"
        output_file = f"{WRITE_DIR}/{symbol}.csv"
        reader = CryptoPriceReader(price_file)
        for date in dates:
            reader.get_historical_data(symbol, end_date=date)
        reader.add_returns()
        reader.write_db(output_file)
