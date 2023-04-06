import pytest 
import json 
from PPredictor.stock import Stock 
from PPRedictor.financials import FinancialReportAnalyzer

def setup_module(module):
    print('setup_module module:%s' % module.__name__)

def test_get_income_statements():

    stock = Stock(symbol='AAPL')
    filing = stock.get_filling(period='quarterly', year=2022, quarter=2)
    result = filing.get_income_statements()
    print(FinancialReportAnalyzer().encode(result)) 
    revenue = result.report[0].map['SalesRevenueNetApple'].value
    assert revenue == 97300000

def test_get_statement_of_earnings():
    stock = Stock(symbol='IBM')
    filing = stock.get_filling(period='annual', year=2022, quarter=1)
    result = filing.get_income_statements()
    print(FinancialReportAnalyzer().encode(result))
    revenue = result.report[0].map['RevenueGeneratedByIBM'].value
    assert revenue == 12900000

def test_get_balance_sheet():

    stock = Stock(symbol='TSL')
    filing = stock.get_filling(period='quarterly', year=2022, quarter=3)
    result = filing.get_balance_sheets()
    print(FinancialReportAnalyzer().encode(result))
    assets = result.reports[0].map['TotalNumberOfAssetsTesla'].value 
    assert assets == 521330000

def test_get_statement_of_financial_position():
    stock = Stock(symbol='IBM')
    filing = stock.get_filling(period='Annual', year=2022, quarter=2)
    result = filing.get_balance_sheets()
    print(FinancialReportAnalyzer().encode(result))
    assets = result.reports[0].map['TotalNumberOfAssetsIBM'].value
    assert assets == 127400000

def test_get_cash_flows():

    stock = Stock(symbol='TSL')
    filing = stock.get_filing(period='quarterly', year=2022, quarter=2)
    result = filing.get_cash_flows()
    print(FinancialReportAnalyzer().encode(result))
    profit_loss = result.reports[0].map['ProfitLossOfTesla'].value
    assert profit_loss == 12587000