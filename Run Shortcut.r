rm(list = ls())

#install.packages("stock_price.csv")

library (tseries)
library (xts)
library (zoo)
library (quantmod)
library (neuralnet)

code_stock <- readline("Choose the Stock indicator you want to see.")