import datetime 
import time 
import pytz 
import logging 
import json 
import pickle 
from kafka import KafkaProducer
from collections import defaultdict 
from config import tokens, time_zone, kafka_config, event_list 
from config import get_cot, get_vix, get_stock_volume
from getMarketData import GetData, get_market_calendar
from economic_indicators_spider import run_indicator_spider 
from cot_reports_spider import run_cot_spider 
from vix_spider import run_vix_spider

def get_data_point(source, tokens, timestamp, request=None, function=None, symbol=None, interval=None, \
                   output_format='json'):
    """Performs a single API call from the token data source."""
    get = GetData(tokens, output_format)
    if source == 'IEX':
        raw_data = get.get_iex_data(request, timestamp)
    elif source == 'AV':
        raw_data = get.get_av_data(timestamp, function, symbol, interval, request)
    else:
        logging.warning('Source isnt recognised')
    return raw_data 

def last_day_of_month(date):
    if date.month == 12:
        return date.replace(day=31)
    return date.replace(month=date.month+1, day=1) - datetime.timedelta(days=1)

def market_hour_to_dt(current_datetime, hour_str):
    dt = datetime.datetime.strptime(hour_str, '%H:%M')
    mh = dt.hour 
    mm = dt.minute 
    dt = current_datetime.replace(hour=mh, minute=mm, second=0, microsecond=0)
    return dt 

def intraday_data(freq, market_hours, current_datetime, source, tokens, economic_data, cot=False, vix=False, request=None, \
                  function=None, symbol=None, interval=None, output_format='json', get_stock_volume=None):
    
    producer = KafkaProducer(bootstrap_servers=kafka_config['servers'],
        value_serializer=lambda x:
        json.dumps(x).encode('utf-8'))
    
    with open(r"items.pickle", "wb") as output_file:
        pickle.dump(defaultdict(), output_file)

    while (current_datetime >= market_hours['market_start']) and (current_datetime <= market_hours['market_end']):

        try:

            process_start_time = time.time()

            market_data = get_data_point(source, tokens, current_datetime, request=request, function=function, symbol=symbol, \
                                        interval=interval, output_format=output_format)
            
            if get_stock_volume and (source != 'AV' and function != 'TIME_SERIES_INTRADAY'):
                interval = freq // 60
                interval = '{:d}min'.format(interval)

                if interval in ['1min', '5min', '15min', '30min', '60min']:
                    volume = get_data_point('AV', tokens, current_datetime, function='TIME_SERIES_INTRADAY',
                        symbol=get_stock_volume, interval=interval, output_format=output_format)
                    
                    producer.send(topic=kafka_config['topics'][1], value=volume)

                else:
                    logging.warning('"{}" interval is not supported'.format(interval))

            producer.send(topic=kafka_config['topics'][4], value=market_data)

            run_indicator_spider(economic_data['countries'], economic_data['importance'], economic_data['event_list'], \
                                current_datetime, kafka_config['servers'], kafka_config['topics'][3])
            
            if cot:
                run_cot_spider(economic_data['cot'], current_datetime, kafka_config['servers'], kafka_config['topics'][2])

            if vix:
                run_vix_spider(current_datetime, kafka_config['servers'], kafka_config['topics'][0])

            process_end_time = time.time()
            process_time = process_end_time - process_start_time

            time.sleep(freq - process_time)

            current_datetime = pytz.utc.localize(datetime.datetime.utcnow()).astimezone(time_zone['EST'])

        except KeyboardInterrupt:
            logging.warning('Action suddenly stopped by the user')
            break 

        else:
            logging.warning('Market is closed')
            logging.warning('Current time: {} {}'.format(datetime.datetime.strftime(current_datetime, "%Y-%m-%d %I:%M %p"), \
                current_datetime.tzname()))
            logging.warning('Market trade hours: from {} to {} {}'.format(datetime.datetime.strftime(market_hours['market_start'], \
                "%Y-%m-%d %I:%M %p"), datetime.datetime.strftime(market_hours['market_end'], "%Y-%m-%d %I:%M %p"), \
                market_hours['market_end'].tzname()))
            
def start_day_session(freq, source, tokens, economic_data, cot=False, vix=False, request=None, function=None, symbol=None, \
                    interval=None, output_format='json', get_stock_volume=None):
    
    current_datetime = pytz.utc.localize(datetime.datetime.utcnow()).astimezone(time_zone['EST'])
    current_date = current_datetime.date()

    market_calendar = get_market_calendar()

    market_day = list(filter(lambda date_dict: date_dict.get('date') == current_date.strftime('%Y-%m-%d'), \
                        market_calendar))[0]
    is_open = market_day.get('status') == 'open'

    if is_open:

        if source == 'IEX':
            premarket_start, premarket_end = market_day.get('premarket').values()
            market_start, market_end = market_day.get('open').values()
            postmarket_start, postmarket_end = market_day.get('postmarket').values()

            hours = [('premarket_start', premarket_start), ('premarket_end', premarket_end), ('market_start', market_start), \
                     ('market_end', market_end), ('postmarket_start', postmarket_start), ('postmarket_end', postmarket_end)]
            market_hours = {key: market_hour_to_dt(current_datetime, value) for key, value in hours}

    else:
        market_hours = {}

        market_start = current_datetime.replace(hour=17, minute=0, second=0, microsecond=0, tzinfo=time_zone['EST'])
        market_hours['market_start'] = market_start - datetime.timedelta(days=(current_datetime.weekday() + 1))

        market_end = current_datetime.replace(hour=16, minute=0, second=0, microsecond=0, tzinfo=time_zone['EST'])
        market_hours['market_end'] = market_end + datetime.timedelta(days=-(current_datetime.weekday() - 4))

    
    intraday_data(freq, market_hours, current_datetime, source, tokens, economic_data, cot=cot, vix=vix, request=request,
                  function=function, symbol=symbol, interval=interval, output_format=output_format,
                  get_stock_volume=get_stock_volume)
    
else:
logging.warning('Current time {} {}'.format(datetime.datetime.strftime(current_datetime, "%Y-%m-%d %I:%M %p"), \
    current_datetime.tzname()))
logging.warning('Today market is closed')

freq = 60 * 5

