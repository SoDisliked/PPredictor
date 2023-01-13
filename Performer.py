from pylab import * 
from scipy import stats 
import numpy as np 
import matplotlib.pyplot as plt 


class ClassificationPerformance:
    names = []
    errors = []

    def __init__(self):
        self.count = 0

    def add(self, name, error_rates):
        self.names.append(name)
        self.errors.append(error_rates)
        self.count += 1

    def compare(self):
        for i in range(self.count):
            for j in range(self.count):
                tst, pvalue = stats.tttest_ind(self.errors[i], self.errors[j])
                if pvalue < 0.05:
                    print("{0} is better than {1}".format(self.names[i], self.names[j]))
                    print("{0} avg err = {1}, {2} avg err = {3}".format(
                        self.names[i], np.average(self.errors[i])
                        self.names[j], np.average(self.errors[j])
                    )):
                else:
                    print("{0} and {1} aren't different after hypothesis testing".format(self.names[i], self.names[j]))

        def make_plot(self):
            plt.figure()
            plt.boxplot(self.errors)
            plt.xlabel(' vs '.join(self.names))
            plt.ylabel('K-fold cross-validation error')
            plt.xticks(range(self.count), self.names)
            plt.show()