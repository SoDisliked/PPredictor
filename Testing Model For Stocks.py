import pandas as pd 
import datetime 

# show data for different entries
start = pd.to_datetime("2020-1-1")
stock = ['APPL']
data = pd.download(stock, start=start, end=datetime.date.today())
print (data)

stock = ['SPX'] 
data = pd.download(stock, start=start, end=datetime.date.today())
print (data)

stock = ['NDQ']
data = pd.download(stock, start=start, end=datetime.date.today())
print (data)

