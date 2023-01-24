public class StockData {
    private String date; // display the date of price
    private String symbol; // display the symbol as it is listed on the stock exchange market

    private double open; // open price
    private double close; // close price
    private double low; // low price
    private double high; // high price
    private double volume; // volume price
    private double adjvalue; // adjvalue price

    public StockData() {}

    public StockData (String date, String symbol, double open, double close, double low, double high, double volume) {
        this.date = date;
        this.symbol = symbol;
        this.open = open;
        this.close = close;
        this.low = low;
        this.high = high;
        this.volume = volume;
    }

    public String getDate() { return date; }
    public void setDate(String date) { this.date = date; }

    public String getSymbol() { return symbol; }
    public void setSymbol(String symbol) { this.symbol = symbol; }

    public String getOpen() { return open; }
    public void setOpen(String open) { this.open = open; }

    public String getClose() { return close; }
    public void setClose(String close) { this.close = close; }

    public String getLow() { return low; }
    public void setLow(String low) { this.low = low; }

    public String getHigh() { return high; }
    public void setHigh(String high) { this.high = high; }

    public String getVolume() { return volume; }
    public void setVolume(String volume) { this.volume = volume; }-

    
}