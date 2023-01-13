import numpy as np 
import pickle 
import matplotlib.pyplot as plt 

def plot_features():
    with open('', 'rb') as f:
        feature_selection = pickle.load(f)

    n = 30
    feature_mean_errors = []
    for featureNo in range(n):
        mean_error = np.average(np.ravel([y for (x,y) in feature_selection["results"] if featureNo in x]))
        print("Feature {0} -> Mean error = {1}".format(featureNo, mean_error))
        feature_mean_errors.append(mean_error)

    print("Selected features: {0}".format(feature_selection["features"]))
    print("Feature mean errors: {0}".format(feature_mean_errors))

    features_figure = plt.figure()
    ax = plt.subplot(10)
    feature_nos = range(len(feature_mean_errors))
    ax.bar(feature_nos, feature_mean_errors, width=0.5, align='center')
    plt.xticks(feature_nos, feature_nos)
    features_figure.show()
    features_figure.waitfobuttonpress()

def rrn_iter_error_plot():
    with open('', 'rb') as f:
        errors = pickle.load(f)

    
    print("Train ERRORS: {0}".format(errors["train"]))
    print("Test ERRORS: {0}".format(errors["test"]))

    plt.figure()
    plt.title("RNN error X iteration trajectory")
    plt.plot(errors["train"])
    plt.plot(errors["train"])
    plt.xlabel("iteration * 10", "trajectory * 10")
    plt.ylabel("error rate after xlabel operation")
    plt.show()

def mlp_iter_error_plot():
    with open('', 'rb') as f:
        errors = pickle.load(f)

    print("Train ERRORS: {0}".format(errors["train session"]))
    print("Train TEST: {0}".format(errors["test session"]))
    plt.figure()
    plt.title("RNN error while ploting X iteration trajectory")
    plt.plot(errors["train"])
    plt.plot(errors["test"])
    plt.xlabel("iteration * 10", "trajectory * 10")
    plt.ylabel("error rate after xlabel operation")
    plt.show()