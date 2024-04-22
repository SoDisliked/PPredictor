import requests 
import json 
import pandas as pd 
import io 
import datetime 
import logging 
from config import time_zone

def change_keys(obj, old, new):
    if isinstance(obj, dict):
        new_obj = obj.__class__()
        for k, v in obj.items():
            new_obj[k.replace(old, new)] = change_keys(v, old, new)
    elif isinstance(obj, (list, set, tuple)):
        new_obj = obj.__class__(change_keys(v, old, new) for v in obj)
    else:
        return obj 
    
    return new_obj

def to_number(v):
    try:
        if v.isdigit():
            return int(v)
        else:
            return float(v)
    except ValueError:
        return v
    
def value_to_number(obj):
    if isinstance(obj, dict):
        new_obj = obj.__class__()
        for k, v in obj.items():
            if isinstance(v, dict):
                new_obj[k] = value_to_number(v)
            elif isinstance(v, (list, set, tuple)):
                new_obj[k] = v.__class__(to_number(lv) for lv in v)
            else:
                new_obj[k] = to_number(v)

    elif isinstance(obj, (list, set, tuple)):
        new_obj = obj.__class__(value_to_number(lv) for lv in obj)
    else:
        return obj 
    
    return new_obj 


class GetData:
    def __init__(self, token, output_format='json'):

        self.__token = token 
        self.output_format = output_format

        assert (output_format == 'json' or output_format == 'csv'), '{} format is not supported'\
            .format(output_format)
        
    def get_iex_data(self, request, timestamp):
        self.url = 'https://cloud.iexapis.com/v1{request}token={token}&format={output_format}'\
            .format(request=request, token=self.__token['iex_token'], output_format=self.output_format)
        
        try:
            req = requests.get(self.url)

            if self.output_format == 'json':
                raw_data = json.loads(req.content)
            else:
                raw_data = pd.read_csv(io.StringIO(req.content.decode('utf-8')))

            if isinstance(raw_data, dict):
                raw_data['Timestamp'] = datetime.datetime.strftime(timestamp, "%Y-%m-%d %H:%M:%S")

                if '/deep/book' in request:
                    symbol = list(raw_data.keys())[0]

                    for i, level in enumerate(raw_data[symbol]['bids']):
                        raw_data['bids_{:d}'.format(i)] = {'bid_{:d}'.format(i): level['price'],
                                                           'bid_{:d}_size'.format(i): level['size']}
                        
                    for i, level in enumerate(raw_data[symbol]['asks']):
                        raw_data['asks_{:d}'.format(i)] = {'ask_{:d}'.format(i): level['price'],
                                                           'ask_{:d}_size'.format(i): level['size']}
                        
                    del raw_data[symbol]

            if isinstance(raw_data, list):
                for mssg in raw_data:
                    mssg['Timestamp'] = datetime.datetime.strftime(timestamp, "%Y-%m-%d %H:%M:%S")

        except requests.exceptions.ConnectionError as mssg:
            print(mssg)

        return raw_data 


def get_av_data(self, timestamp, function=None, symbol=None, interval=None, request=None):
    if not request:
        if function in ['FX_INTRADAY', 'FX_DAILY', 'FX_WEEKLY', 'FX_MONTHLY']:
            symbol1, symbol2 = symbol[:3], symbol[3:]
            self.url = 'https://www.alphavantage.co/query?function={function}&from_symbol={symbol1}'\
                '&to_symbol={symbol2}&interval={interval}&apikey={token}&datatype={output_format}'\
                .format(function=function, symbol1=symbol1, symbol2=symbol2, interval=interval, \
                        token=self.__token['av_token'], output_format=self.output_format)

        else:
            self.url = 'https://www.alphavantage.co/query?function={function}&symbol={symbol}'\
                '&interval={interval}&apikey={token}&datatype={output_format}'\
                .format(function=function, symbol=symbol, interval=interval, token=self.__token['av_token'],\
                        output_format=self.output_format)
    else:
        self.url = 'https://www.alphavntage.co/query?' + request + '&apikey={token}&datatype={output_format}'\
            .format(token=self.__token['av_token'], output_format=self.output_format)
        
    try:
        req = requests.get(self.url)
        if self.output_format == 'json':
            raw_data = json.loads(req.content)

            if not raw_data:
                raise Exception('Alpha advantage API isnt available')
            
            if 'Error message' in raw_data:
                raise Exception(raw_data['Error message'])
            
            keys_level_1 = list(raw_data.keys())
            last_dt_str = list(raw_data[keys_level_1[1]].keys())[0]

            last_dt = datetime.datetime.strptime(last_dt_str, "%Y-%m-%d %H:%M:%S")
            last_dt = time_zone['EST'].localize(last_dt)

            raw_data = raw_data[keys_level_1[1]][last_dt_str]

            if last_dt < timestamp - datetime.timedelta(minutes=4):
                logging.warning('RETURNED DATA IS DELAYED')
                raw_data['Timestamp'] = datetime.datetime.strftime(timestamp, "%Y-%m-%d %H:%M:%S")
            else:
                raw_data['Timestamp'] = datetime.datetime.strftime(timestamp, "%Y-%m-%d %H:%M:%S")

        else:
            raw_data = pd.read_csv(io.StringIO(req.content.decode('utf-8')))

            if 'Error message' in raw_data.iloc[0, 0]:
                raise Exception(raw_data.iloc[0, 0])
            
            raw_data = raw_data.iloc[0:1, :]
            last_dt_str = raw_data.loc[0, 'Timestamp']
            last_dt = datetime.datetime.strptime(last_dt_str, "%Y-%m-%d %H:%M:%S")
            last_dt = time_zone['EST'].localize(last_dt)

            if last_dt < timestamp - datetime.timedelta(minutes=4):
                logging.warning('RETURNED DATA IS DELAYED')
                raw_data.iloc[0, 'Timestamp'] = datetime.datetime.strftime(timestamp, "%Y-%m-%d %H:%M:%S")
            else:
                raw_data.iloc[0, 'Timestamp'] = datetime.datetime.strftime(timestamp, "%Y-%m-%d %H:%M:%S")

        raw_data = change_keys(raw_data, ".", "_")

        raw_data = value_to_number(raw_data)

        return raw_data
    
    except requests.exceptions.ConnectionError as msg:
        print(msg)


def get_market_calendar():
    response = requests.get('https://capital.com/trading/platform/',
        headers={'Authorization': 'Bearer <TOKEN>', 'Accept': 'application/json'})
    return response.json()['calendar']['days']['day']
