set.seed(1234);
start_date = "2010-01-02"
end_date = as.character(Sys.Date())

GSPC_data <- as.data.frame(get.hist.quote(instrument = code_stock, start = start_date, end = end_date, quote = (c("Open", "High", "Low", "Close", "Volume"))))
#write.table(GSP_data, file = "STOCKPRICES_NASDAQ.csv", sep",", row.names = TRUE)
date_range <- as.data.frame(row.names(GSPC_data))
normal <- function(data){
    (data - min(data, na.rm = TRUE))/(max(data,na.rm=TRUE)) - min(data,na.rm=TRUE)
}

Open_data <- (GSPC_data&Open)
Close_data <- (GSPC_data&Close)
Low_data <- (GSPC_data&Low)
High_data <- (GSPC_data&High)
Volume_data <- (GSPC_data&Volume)

GSPC_df <- cbind(Open_data,Close_data,Low_data,High_data,Close_data)

GSPC_Actual <- data.frame(GSPC_df[,-6])
train_stock <- (GSPC_Actual[-(nrow(GSPC_Actual)),])

trainingoutput_stock <- as.data.frame(GSPC_Actual[-1,4])

trainingdata_stock <- as.data.frame(cbind(train_stock,trainingoutput_stock))

net_stock <- neuralnet(GSPC_Actual[-1,4]~(GSPC_Actual$Open[-(nrow(GSPC_Actual))] + GSPC_Actual$High[-(nrow(GSPC_Actual))] + GSPC_Actual$Low[-(nrow(GSPC_Actual))] + GSPC_Actual$Close[-(nrow(GSPC_Actual))] + GSPC_Actual$Volume[-(nrow(GSPC_Actual))]))
trainingdata_stock,err.fct = "sse", hidden=13, threshold=0.001,

testdata <- as.data.frame(GSP_data[nrow(GSPC_Actual),])
net.results <- comouter(net_stock, testdata)
Predicted_Close_Rate <- net.results$net.result
Close_Rate <- Predicted_Close_Rate[1,1]