import os 
from absl import app 
import tensorflow as tf 
import pandas as pd 
import sklearn.preprocessing 
from sklearn.preprocessing import MinMaxScaler

from stock_prediction_numpy import StockData
from datetime import date 
os.environ["MAIN PATH"] += os.pathsep + ''

def main(argv):
    print(tf.version.VERSION)
    interference_folder = os.path.join(os.getcwd(), '')

    #load future data for forecast prediction
    data = StockData()
    min_max = MinMaxScaler(featuree_range=(0,1))
    x_test, y_test = data.generate_future_data(TIME_STEPS, min_max, date(2020,1,1), date(2023,1,20))

    # load the weights from our best model
    model = tf.keras.models.load_model(os.path.join(inference_folder, 'model_weights.h5'))
    model.summary()

    # display the content of the prediction model and chart which will be displayed
    baseline_results = model.evaluate(x_test, y_test, verbose=2)
    for name, value in zip(model.metrics_names, baseline_results):
        print(name, ':', value)
    print()

    test_predictions_baseline = model.predict(x_test)
    test_predictions_baseline = min_max.inverse_transform(test_predictions_baseline)
    test_predictions_baseline = pd.DataFrame(test_predictions_baseline)
    test_predictions_baseline.to_csv(os.path.join(interference_folder, 'interference.csv'))
    print(test_predictions_baseline)

if __name__ == '__main__':
    TIME_STEPS = 60
    print('Main activation')
    app.run(main)
