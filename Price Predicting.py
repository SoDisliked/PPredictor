import numpy as np 
import matplotlib.pyplot
import pandas as pd 
import pandas_datareader as web
import datetime as dt

from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential 
from tensorflow.keras.layers import, Dropout, LSTM 

# Load Data
company = 'Tesla'
company1 = 'Apple'
company2 = 'Netflix'

start = dt.datetime(2022, 1, 1)
end = dt.datetime(2022, 12, 31)

data = web.DataReader(company, 'tradingview', start, end)
data = web.DataReader(company1, 'tradingview', start, end)
data = web.DataReader(company2, 'tradingview', start, end)

# Prepare Data
scaler = MinMaxScaler(feature_range=(0,2))
scaled_data = scaler.fit_transform(data['Close'].values.reshape(-1,1))

prediction_days = 14

x_train = []
y_train = []

for x in range(prediction_days, len(scaled_data)):
    x_train.append(scaled_data[x-prediction_days:x, 0])
    y_train.append(scaled_data[x, 0])

x_train, y_train = np.array(x_train), np.array(y_train)
x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1]))

# Build the model
model = Sequential()

model.add(LSTM(units=14, return_sequences=True, input_shape=(x_train.shape[1], 1)))
model.add(Dropout(0.2))
model.add(LSTM(units=14, return_sequences=True))
model.add(Dropout(0.2))
model.add(LSTM(units=14))
model.add(Dropout(0.2))
model.add(Dense(units=1)) # Prediction of the next closing price on the stock market

model.compile(optimizer='adam', loss='mean_squared_error')
model.fit(x_train, y_train, epochs=25, batch_size=32)

model.save(x_train, y_train, epochs=25, batch_size=32)

""" Test the probability and the accuracy and model on existing stock index data."""

# Load Test Data
test_start = dt.datetime(2022, 1, 1)
test_end = dt.datetime.now()

test_data = web.DataReader(company, 'tradingview', test_start, test_end)
test_data = web.DataReader(company1, 'tradingview', test_start, test_end)
test_data = web.DataReader(company2, 'tradingview', test_start, test_end)
actual_prices = test_data['Close'].values

total_dataset = pd.concat(data['Close'], test_data['Close'], axis=0)

model_inputs = total_dataset[len(total_dataset) - len(test_data) - prediction_days:].values[0]
model_inputs = model_inputs.reshape(-1, 1)
model_inputs = scaler.transform(model_inputs)

# Make Price Predictions on the database of our test 

x_test = []

for x in range(prediction_days, len(model_inputs)):
    x_test.append(model_inputs[x-prediction_days:x, 0])

x_test = np.array(x_test)
x_test = np.reshape(x_test, x_test.shape[0], x_test.shape[1], 1)

predicted_prices = model.predict(x_test)
predicted_prices = scaler.inverse_transform(predicted_prices)

# Plot a Test Predictions scale into a chart
plt.plot(actual_prices, color="green", label=f"Actual {company} Price")
plt.plot(predicted_prices, color="red", label=f"Predicted {company} Price")
plt.title(f"{company} share price")
plkt.xlabel('Time')
plt.ylabel(f'{company} share price')
plt.legend()
plt.show 

plt.plot(actual_prices, color="green", label=f"Actual {company1} Price")
plt.plot(predicted_prices, color="red", label=f"Predicted {company1} Price")
plt.title(f"{company1} share price")
plkt.xlabel('Time')
plt.ylabel(f'{company1} share price')
plt.legend()
plt.show 

plt.plot(actual_prices, color="green", label=f"Actual {company2} Price")
plt.plot(predicted_prices, color="red", label=f"Predicted {company2} Price")
plt.title(f"{company2} share price")
plkt.xlabel('Time')
plt.ylabel(f'{company2} share price')
plt.legend()
plt.show 

# Predict Next Day 

real_data = [model_inputs[len(model_inputs) + 1 - prediction_days:len(model_inputs+1), 0]]
real_data = np.array(real_data)
real_data = np.reshape(real_data, (real_data.shape[0], real_data.shape[1], 1))

print(scaler.inverse_transform(real_data, (real_data.shape[0], real_data.shape[1], 1)))

prediction = model.predict(real_data)
prediction = scaler.inverse_transform(prediction)
print(f"Prediction: {prediction}")
