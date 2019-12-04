# generate gaussian data
from numpy.random import seed
from numpy.random import randn
from numpy import mean
from numpy import std
import numpy as np
from matplotlib import pyplot
from scipy.stats import shapiro
from statsmodels.graphics.gofplots import qqplot
import scipy



# based on https://machinelearningmastery.com/a-gentle-introduction-to-normality-tests-in-python/

# # seed the random number generator
# seed(1)
# # generate univariate observations
# data = 5 * randn(100) + 50

# read data from a file
filename = 'OD_Sampels_M1.csv'
with open(filename, 'r') as f:
    data = f.readlines()
    data = [float(i.strip('\n')) for i in data]
    data = np.array(data)
print(data)
# summarize
print('mean=%.3f stdv=%.3f' % (mean(data), std(data)))


# histogram plot
pyplot.hist(data)
pyplot.show()

# QQ Plot
# q-q plot
qqplot(data, line='s')
pyplot.show()


# Shapiro-Wilk Test
# seed the random number generator
# normality test
stat, p = shapiro(data)
print('Statistics=%.3f, p=%.3f' % (stat, p))
# interpret
alpha = 0.05
if p > alpha:
    print('Sample looks Gaussian (fail to reject H0)')
else:
    print('Sample does not look Gaussian (reject H0)')

# variance estimation
data_var = np.var(data)
print ('Sample variance: %f'%data_var)


# Determine the number of sample
# https://stats.stackexchange.com/questions/341358/how-many-samples-do-i-need-to-estimate-a-gaussian-distribution

# SUPPORTED CONFIDENCE LEVELS: 50%, 68%, 90%, 95%, and 99%
confidence_level_constant = {50: .67, 68: .99, 90: 1.64, 95: 1.96, 99: 2.57}


margin_of_error = 10
confidence_level = 95
n = (confidence_level_constant[confidence_level]/margin_of_error)**2*data_var

print("SAMPLE SIZE: %d" % n)


data2 = 5 * randn(100) + 50

F = np.var(data) / np.var(data2)
df1 = len(data) - 1
df2 = len(data2) - 1


alpha = 0.05 #Or whatever you want your alpha to be.
p_value = scipy.stats.f.cdf(F, df1, df2)
print(p_value)
if p_value > alpha:
    print('Reject the null hypothesis that Var(X) == Var(Y)')