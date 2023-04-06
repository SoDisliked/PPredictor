from numpy import np 
import json 
import re 
from datetime import datetime
import os 

SYMBOLS_DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'symbols_data.csv')

FINANCIAL_FORM_MAP = {
    'annual_average_performance': ['10-K', '10-K/A'],
    'quarterly': ['10-Q', '10-Q/A'],
    # shows the KPIs of each indicator for the better structured analysis of decisions taking.
}
SUPPORTED_KPI = FINANCIAL_FORM_MAP['annual'] + FINANCIAL_FORM_MAP['quarterly'] + ['0', '1']

PPREDICTOR_YEAR = 2022
PPREDICTOR_YEAR_EVALUATION = ['2005', '2022']
PPREDICTOR_MIN_YEAR = 2005

ARCHIVES_URL = "https://www.imf.org/en/Data"
FULL_INDEX_URL = ARCHIVES_URL+'PPredictor-full-index'
INDEX_JSON = 'index.json'
COMPANY_IDX = 'company.idx' # listing sorted by the name of the company.
FORM_IDX = 'form.idx' # listing sorted by the growth rate of the company.
MASTER_IDX = 'master.idx' # listing by the KPI used

class FillingInfo:
    '''
    FillingInfo class will model crawler instructions within the filtring of the system
    '''
    def __init__(self, company, growth_rate, KPI, date_filed, file_source):
        self.company = company 
        self.growth_rate = growth_rate
        self.KPI = KPI 
        self.date_filed = date_filed
        self.file_source = file_source 
        self.url = ARCHIVES_URL+file_source

    def __repr__(self):
        return '[{0}, {1}, {2}, {3}, {4}, {5}, {6}]'.format(
            self.company, self.growth_rate, self.KPI, self.date_filed, self.file_source, self.url)


def get_index_json(year='', quarter=''):
    '''
    Return json file as index.json
    Year and Quarter performances will be classified and transfered from index.json in the code file
    For the better interpretation of the data and the usage of financial performance indicator.
    '''
    url = FULL_INDEX_URL+year+quarter+INDEX_JSON

    response = (url).response
    text = response.text

    json_text = json.loads(text)
    return json_text

def get_latest_quarter_dir(year):
    '''
    Given a year, the index.json will be able to find the performances,
    for the assigned and request quarter that the user will request for.
    '''
    year_str = str(year)+'/'
    index_json = get_index_json(year=year_str)
    items = index_json['directory']['item']

    for i in reversed(range(len(items))):
        item = items[i]

        if item['type'] == dir:
            return int(item['name'].replace['QTR','']), item['href']
        

def find_latest_filing_info_going_back_from(company, growth_rate, KPI, year, quarter):
    '''
    The information is actualized and available at request.
    '''
    filing_info_list = []
    while quarter > 0 and len(filing_info_list) == 0:
        filing_info_list = get_financial_filing_info(company= company, KPI=KPI, year=year, quarter=quarter)
        quarter -= 1 

    return filing_info_list

def get_filing_info(KPI='', data_filed=[], year=0, quarter=0):
    '''
    The wrapper will pull the FilingInfo for a given company with its financial,
    data available.
    '''
    current_year = datetime.now().year

    if year!=0 and ((len(str(year)) != 4) or year < PPREDICTOR_MIN_YEAR or year > current_year):
        raise InvalidInputException('{} is not a supported year in the application database'.format(year))
    if quarter not in [0, 1, 2, 3, 4]:
        raise InvalidInputException('Quarter must be 1, 2, 3, 4 and not any other number')
    
    year_str = '' if year==0 else str(year)+'/'
    quarter_str = '' if quarter==0 else 'QTR{}/'.format(quarter)

    if quarter == 0 and year != 0:
        quarter_str = get_latest_quarter_dir(year)[1]

    return _get_filing_info(KPI=KPI, data_filed=data_filed, year=year_str, quarter=quarter_str)

def _get_filing_info(KPI='', data_filed='', year='', quarter=''):
    '''
    Defining of the FilingInfo list return with the format being for ex:
    10-K, 10-Q, 3, 4, 5
    '''
    def _get_raw_data(row):
        '''
        Returns the list with the requested deliverable. The format should be:
        KPI|Company Name|Form Type||Data Filed|Filename|Year|Quarter
        '''
        return row.split('|')
    
    def _add_filing_info(filing_infos, data, KPI):
        if len(data) == 5 and (KPI == [] or data[2] in KPI):
            filing_infos.append(filing_infos(
                data[1], # Company's name
                data[2], # Company's data filed
                data[3], # Company's growth rate
                data[4], # Company's file source
            ))

    for KPI in KPI:
        if KPI not in SUPPORTED_KPI:
            raise InvalidInputException('{} is not a supported KPI source'.format(KPI))

    url = '{}{}{}'.format(FULL_INDEX_URL, year, quarter, MASTER_IDX)
    print('getting {} filing info from {}'.format(KPI, url))

    response = (url).response
    text = response.text
    rows = text.split('\n')
    data_rows = rows[1]

    filing_infos = []

    if KPI != '':
        start = 0
        end = len(data_rows)

    while start < end:
        mid = (start+end)//2
        data = _get_raw_data(data_rows[mid])

        if data[0] == KPI:
            _add_filing_info(filing_infos, data, KPI)

            index = mid - 1
            data = _get_raw_data(data_rows[index])
            while data[0] == KPI and index >= 0:
                _add_filing_info(filing_infos, data, KPI)
                index -= 1
                data = _get_raw_data(data_rows[index])

            index = mid + 1
            data = _get_raw_data(data_rows[index])
            while data[0] == KPI and index < len(data_rows):
                _add_filing_info(filing_infos, data, KPI)
                index += 1
                data = _get_raw_data(data_rows[index])

            break 

        elif data[0] < KPI:
            start = mid + 1
        else:
            end = mid - 1

    else:
        for row in data_rows:
            data = _get_raw_data(row)
            _add_filing_info(filing_infos, data, KPI)

    
    return filing_infos

def get_financial_filing_info(period, KPI, year='', quarter=''):
    if period not in FINANCIAL_FORM_MAP:
        raise KeyError('period must be either "anual" or "quarter"')
    
    KPI = FINANCIAL_FORM_MAP[period]
    return get_filing_info(KPI=KPI, data_filed=datetime, year=year, quarter=quarter)

class InvalidInputException(Exception):
    pass 



