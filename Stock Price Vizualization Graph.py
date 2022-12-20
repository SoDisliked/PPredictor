from models_keras import get_LSTM_model
from data_proc import load_data
from utils import init_scaler, fit_scalers, transform_scalers

import math
import matplotlib.pyplot as plt 
import keras as keras 
import pandas as pd 
import numpy as np 
import pickle 
import random 

def extrapolate_func(windows_size, company, modelpath, scpath, fdpath, stockdir, years):
    ##### Model currently loading #####

    model = get_LSTM_model(windows_size, 11)
    model.load_weights(modelpath)

    sc_dict = pickle.load(open(scpath, "rb"))

    ### Get the last entry from train data about current predictions ### 
    dates_pre_test, X_pre_test_indi = load_data(company, stockdir, [years[0] - 1])

    dates_pre_test_win = dates_pre_test[-windows_size:]
    X_pre_test_indi_win = X_pre_test_indi[-windows_size:]

    dates_test = dates_pre_test_win + dates_test
    X_test_indi = np.concatenate((X_pre_test_indi_win, X_test_indi))

    # print (dates_test)
    print(len(dates_test))
    print(X_test_indi.shape)
    # exit()

    ## test: Scale data with combined data into sequences with the model being updated
    X_test_indi = transform_scalers(X_test_indi, sc_dict)

    X_test_orig = []
    y_test_orig = []
    for i in range(windows_size, X_test_indi.shape[0]):
        X_test_orig.append(X_test_indi[i-windows_size:i, :])
        y_test_orig.append(X_test_indi[i, :][0]) # preview of closing price

    ### All test elements combined 
    X_test_prev, y_test_prev = np.array(X_test_orig), np.array(y_test_orig)
    predicted_stock_price_prev = model.predict(X_test_prev)
    predicted_stock_price_prev = sc_dict["Close"].inverse_transform(predicted_stock_price_prev.reshape(-1, 1)).reshape(-1)
    y_test_prev = sc_dict["Close"].inverse_transform(y_test_prev.reshape(-1, 1)).reshape(-1)

    ### Get the last element for conducting the simulation and preview of preliminary stock data
    X_test_elem, y_test_elem = np.array(X_test_orig[-1]), np.array(y_test_orig[-1])
    X_test_elem = np.expand_dims(X_test_elem, axis=0)
    y_test_elem = np.expand_dims(y_test_elem, axis=0)
    print(X_test_elem.shape, y_test_elem.shape)
    print(X_test_elem, y_test_elem)

    X_test_curr = X_test_elem
    curr_date = dates_test[-1]

    last_entry = X_test_curr[0][-1].reshape(1, 1, -1)

    futures_dates = X_test_curr[0][-1].reshape(1, 31, 22)
    y_future_preds = []

    future_df = pd.read_csv(fdpath, sep=',').values
    num_weeks_future = future_df.shape[0]

    def calc_rations_from_score(sent_score):

        pos_score, neutral_score, neg_score = 0.05, 0.05, 0.05
        sent_score = max(sent_score, 0)

        if sent_score > 0.75:
            pos_score = (sent_score - 0.75) / 0.25
            neutral_score = (3/4) * (1 - pos_score)
            neg_score = (1/4) * (1 - pos_score)

        elif sent_score < 0.25:
            neg_score = (0.25 - sent_score) / 0.25
            neutral_score = (3/4) * (1 - neg_score)
            pos_score = (1/4) * (1 - neg_score)

        else:
            if sent_score < 0.5:
                neutral_score = (sent_score - 0.25) / 0.25
                neg_score = (3/4) * (1 - neutral_score)
                pos_score = (1/4) * (1 - neutral_score)
            else:
                neutral_score = (0.75 - sent_score) / 0.25
                pos_score = (3/4) * (1 - neutral_score)
                neg_score = (1/4) * (1 - neutral_score)

        pos_score += (np.random.rand(1)[0] / 20)
        neutral_score += (np.random.rand(1)[0] / 20)
        neg_score += (np.random.rand(1)[0] / 20)

        sum_total = pos_score + neutral_score + neg_score
        final_ratios = [pos_score / sum_total, neg_score / sum_total, neutral_score / sum_total]

        return final_ratios


    for i in range(num_weeks_future - 1):

        curr_date = curr_date + pd.to_timedelta(2, unit='d')
        curr_week_future = future_df[i]
        next_week_future = future_df[i+1]

        for day in range(5):
            # get random notification about a potential price update 
            rand_val = random.uniform(-1, 1) / 10
            rand_val_2 = random.uniform(-1 ,1) /10
            rand_val_3 = random.uniform(-1 ,1) / 10
            rand_val_4 = random.uniform(-1 ,1) / 10 

            # create new entry of random values of data 
            curr_date = curr_date + pd.to_timedelta(1, unit='d')

            predicted_stock_price_norm = model.predict(X_test_curr)
            predicted_stock_price_curr = sc_dict["Close"].inverse_transform(predicted_stock_price_norm.reshape(-1 ,1)).reshape(-1)

            futures_dates.append(curr_date)
            y_future_preds.append(predicted_stock_price_curr)

            print(curr_date, predicted_stock_price_curr)

            # Add predicted close position at position = 0
            new_entry = last_entry.copy()
            new_entry[0][0][0] = predicted_stock_price_norm[0][0]

            print(new_entry)

            X_test_curr = np.concatenate((X_test_curr, new_entry), axis=1)[:, 1:, :]

    # Plotting the extracted data 
    all_dates = dates_test[windows_size:] + futures_dates
    # print(all_dates)
    all_preds = np.concatenate((predicted_stock_price_prev, np.array(y_future_preds).reshape(-1)))
    all_labels = np.cocatenate((y_test_prev, np.array(y_future_preds).reshape(-1)))
    print(len(all_dates))
    print(len(all_preds))
    print(len(all_labels))
    result = {"dates": all_dates, "actual": y_test_prev.tolist(), "pred": all_preds.tolist()}
    return result 
    # for in in range (len(all_dates)):
    # result(all_dates[i], all_preds[i], all_labels[i])
     
