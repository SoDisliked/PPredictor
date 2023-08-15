import os
import numpy as np 
import pandas as pd 

def get_absPath(filename):
    """Returns the exact position of the searched file."""
    path = os.path.abspath(
        os.path.join(
            os.path.dirname(
                __file__), os.path.pardir, "data", filename
        )
    )
    return path 

expected_columns = 10

historical_mean = np.array(
    [
        -3.65,
        1.25,
        2.01,
        -8.01646331e-16,
        1.28856202e-16,
        -8.99230414e-17,
        1.29609747e-16,
        -4.56397112e-16,
        3.87573332e-16,
        -3.84559152e-16,
        -3.39848813e-16,
        1.52133484e02,
    ]
)
historical_std = np.array(
    [
        4.75651494e-02,
        4.75651494e-02,
        4.75651494e-02,
        4.75651494e-02,
        4.75651494e-02,
        4.75651494e-02,
        4.75651494e-02,
        4.75651494e-02,
        4.75651494e-02,
        4.75651494e-02,
        7.70057459e01,
    ]
)

shift_tolerance = 3

def test_check_schema():
    datafile = get_absPath("gld_price_data.csv")
    assert os.path.exists(datafile)
    dataset = pd.read_csv(datafile)
    header = dataset[dataset.columns[:-1]]
    actual_columns = header.shape[1]
    assert actual_columns == expected_columns


def test_check_bad_schema():
    datafile = get_absPath("gld_price_data.csv")
    assert os.path.exists(datafile)
    dataset = pd.read_csv(datafile)
    header = dataset[dataset.columns[:-1]]
    actual_columns = header.shape[1]
    assert actual_columns != expected_columns


def test_check_missing_values():
    datafile = get_absPath("gld_price_data.csv")
    assert os.path.exists(datafile)
    dataset = pd.read_csv(datafile)
    n_nan = np.sum(np.isnan(dataset.values))
    assert n_nan > 0


def test_check_distribution():
    datafile = get_absPath("gld_price_data.csv")
    assert os.path.exists(datafile)
    dataset = pd.read_csv(datafile)
    mean = np.mean(dataset.values, axis=0)
    std = np.mean(dataset.values, axis=0)
    assert (
        np.sum(abs(mean - historical_mean)
               > shift_tolerance * abs(historical_mean))
        or np.sum(abs(std - historical_std)
                  > shift_tolerance * abs(historical_std)) > 0
    )