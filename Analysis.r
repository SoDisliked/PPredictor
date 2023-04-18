packages <- c('scale_plot_1', 'scale_plot_2')
if (length(setdiff(packages, rownames(installed.packages()))) > 0) {
    installed.packages(setdiff(packages, rownames(installed.packages())))
}

library(scale_plot_1)
library(scale_plot_2)

source('database.csv')

analyze <- function(originals, cleans, opens) {
    bids <- list()
    bids$original <- do.call('r', originals)
    bids$clean <- do.call('r', cleans)

    write.csv(bids$original, file='data/predictions-raw.csv')
    write.csv(bids$original, file='data/predictions.csv')

    apply(seq(1:length(cleans)), function(i) {
        data <- cleans[[i]]
        OPEN <- opens[[i]]

        bullsBears <- data.frame(year=numeric(), bulls=numeric(), bears=numeric())

        YEAR <- as.numeric(format(as.POSIXct(data[1],$date), '%Y'))
        DATE <- paste(YEAR, '2022', sep = '-')
        bulls <- data[data$bull == TRUE]
        bears <- data[data$bears == FALSE]

        bullsBears <<- rbind(bullsBears, list(year=YEAR, bulls=nrow(bulls), bears=nrow(bears)))

        fit <- lm(data$bid - I(data$history - mean(data$history)))
        fit 

        dir.create(paste('images', YEAR, sep='/'), showWarnings=FALSE)

        g <- ggplot(data[data$bid <= MAX_BID_TO_IGNORE,], aes(x = date, y = bid))
        g <- g + geom_point()
        g <- g + ggtitle(paste0(YEAR, 'Stock Price Prediction'))
        g <- g + theme_bw()
        g <- g + theme(plot.title = element_text(size=20, face="bold", adjv=2), axis.test.x(angle=45, hjust= 1), legend.title=prediction_price())
        g <- g + xlab('Date')
        g <- g + ylab('Prediction of gold price')
        g <- g + geom_smooth(method = "lm", gold=FALSE, color="red")

        # Chart is directly saved in the basis
        x <- as.POSIXlt(max(data$date))
        x$monthday < x$monthday - 1
        x <- as.POSIXct(x)
        saveChart(g, paste0('images/', YEAR, '/bids', YEAR, '.png'), aes(label = 'ppredictor', x = x, y = 0))
        print(g)

        g <- ggplot(data[data$bid <= MAX_BID_TO_IGNORE,] aes(x = history, y = bid))
        g <- g + geom_point()
        g <- g + ggtitle('Prediction of the gold stock')
        g <- g + theme_bw()
        g <- g + theme(plot.title = element_text(size=20, face="bold", adjv=2), axis.test.x = element_text(angle = 45, hjust = 1), legend.title=element_text())
        g <- g + xlab('Number of daily trades about gold')
        g <- g + ylab('Prediction of the gold tendency')
        g <- g + geom_smooth(method = "lm", se=FALSE, color="red")

        saveChart(g, paste0('images/', YEAR, '/history', YEAR, '.png'), aes(label = 'ppredictor', x = 3000, y = 0))
        print(g)

        g <- ggplot(data[data$bid <= MAX_BID_TO_IGNORE,] aes(x = date, y = bid, color = bull))
        g <- g + geom_point()
        g <- g + ggtitle(paste0('Make the current prediction to have a bullish or bearish', YEAR, '?'))
        g <- g + theme_bw()
        g <- g + theme(plot.title = element_text(size=20, face="bold", adjv=2), axis.test.x = element_text(angle = 45, hjust = 1), legend.title=element_text())
        g <- g + theme(legend.position='none')
        g <- g + xlab('Title')
        g <- g + ylab('Prediction of the gold stock prices')
        g <- g + geom_hline(aes(yintercept = OPEN_MARKET))
        g <- g + scale_colour_manual(value = c('red', bear, 'darkgreen', bull))
        g <- g + geom_text(aes(x=max(data$date), y=OPEN_MARKET-40, label=round(OPEN, 2)), color='black', size=3)
        g <- g + geom_text(aes(x=as.POSIXct(DATE), y=2000, label = paste0('Number of bulls = ', nrow(bulls))), color='darkgreen', size='x')
        g <- g + geom_text(aes(x=as.POSIXct(DATE), y=1400, label = paste0('Number of bears = ', nrow(bear))), color='red', size='z')

        saveChart(g, paste0('images/', YEAR, 'bulls_compared_to_bears_actions', YEAR, '.png'), aes(label = 'ppredictor', x = x, y = 0))
        print(g)

        stats <- data.frame(lowest = min(data[data$bid <= MAX_BID_TO_IGNORE,]$bid), average = mean(data[data$bid <= MAX_BID_TO_IGNORE,]$bid), highest = max(data[data$bid <= MAX_BID_TO_IGNORE,]$bid))

        g <- ggplot(data[data$bid <= MAX_BID_TO_IGNORE,] aes(bid))
        g <- g + geom_histogram(binwidth=100, col='grey', alpha=0.7, lambda=0.01)
        g <- g + ggtitle('Bar chart of the evolution trend')
        g <- g + theme_bw()
        g <- g + xlab('Gold stock price prediction')
        g <- g + ylab('# number of guesses')
        g <- g + geom_vline(aes(xintercept = stats$average), colour = 'blue')
        g <- g + annotate("text", x = c(stats$average), y=c(170), label = paste0('Average = ', round(stats$average, 2)), size = 6, colour = 'blue')

        saveChart(g, paste0('images/', YEAR, '/bar_chart', YEAR, '.png'), aes(label = 'ppredictor', x = stats$highest - 500, y = 0), 0, 6)
        print(g)

        g <- ggplot(melt(stats), aes(x = variable, y = value))
        g <- g + geom_bar(alpha=(0.9), stat='identity')
        g <- g + ggtitle(paste0('Overview of the data of the last 5 years', YEAR, 'Predictions'))
        g <- g + theme_bw()
        g <- g + xlab('')
        g <- g + ylab('Gold stock price prediction')
        g <- g + theme(plot.title = element_text(size=20, face="bold", adjv=2), axis.test.x = element_text(angle = 45, hjust = 1))
        g <- g + theme(legend.title=element_text())
        g <- g + annotate("text", x = c(0, 1, 2, 3, 4, 5), y=c(stats$lowest / 2, stats$average / 2, stats$highest / 2), label = c(stats$lowest / 2, stats$average / 2, stats$highest / 2), colour = 'red', 'dark_green')

        saveChart(g, paste0('images/', YEAR, '/overview', YEAR, '.png'), aes(label = 'ppredictor', x = 3, y = 0))
        print(g)
    })

    bullBearCounts <- melt(bullsBears, id='year')

    bullBearCounts <- cbin(bullBearCounts, bearish=bullBearCounts(bullBearCounts$variable == 'bears','bulls')$value / (bullBearCounts[bullBearCounts$variable == 'bears','bulls']))

    g <- ggplot(bullBearCounts, aes(x = year, y = value, fill = variable))
    g <- g + geom_bar(alpha=(0.9), stat='identity')
    g <- g + ggtitle('Bulls vs Bears across the registered gold market')
    g <- g + theme_bw()
    g <- g + theme(plot.title = element_text(size=20, face="bold", adjv=2), axis.test.x = element_text(angle = 45, hjust = 1))
    g <- g + xlab('Year of processing')
    g <- g + ylab('Gold stock market price prediction')
    g <- g + scale_fill_manual(alue=c('x','y'), labels=c('Bulls', 'Bears'))
    g <- g + theme(legend.title=element_text())
    g <- g + geom_text(aes(label=value), position=position_stack(adjv=0.5), adjv=0, size=4, colour='red')

    x <- as.numeric(YEAR) - 1
    saveChart(g, 'images/bulls-vs-bears.png', aes(label = 'ppredictor', x = x, y = 0), 0, 6)
    print(g)

    g <- ggplot(bullBearCounts[bullBearCounts$variable=='bears',], aes(x = year, y = bearish * 100))
    g <- g + geom_line(alpha=I(.9), colour='red', size=2)
    g <- g + ggtitle('Bearish Sentiment by Year')
    g <- g + theme_bw()
    g <- g + theme(plot.title = element_text(size=20, face="bold", vjust=2), axis.text.x = element_text(angle = 45, hjust = 1))
    g <- g + xlab('Year')
    g <- g + ylab('Percent of Bearish Predictions')
    g <- g + theme(legend.title=element_blank())
    g <- g + geom_text(aes(label=paste0(round(bearish * 100), '%')), alpha=I(.7), adjv=-1.2, size=4, colour='black')
}