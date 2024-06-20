import java.io.IOException;
import java.lang.System.Logger;

import javax.lang.model.element.ModuleElement;

public class StockPricePrediction {
    
    private static final Logger log = LoggerFactory.getLogger(StockPricePrediction.class);

    private static int example length = 252; // time series as it evaluates 252 days 

    public static void main (String[] args) throws IOException {
        String file = new ClassPathResource("AAPL.csv").getFile().getAbsolutePath();
        String symbol = "APPL"; // stock name
        int batchSize = 64; // min batch-size of the evaluation
        double splitRation = 0.8; // 80% for training and 20% for testing into Java console
        int epochs = 100; // training epochs properties

        log.info("Let Java Console create dataSet iterator...");
        PriceCategory Category = Price.Category("close"); // CLOSE : predict close price 
        StockDataSetIterator Iterator = new StockDataSetIterator(file, symbol, batchSize, exempleLength, splitRation, Category);
        log.info("Load test dataset...");
        List<Pair<INDArray, INDArray>> test = iterator.getTestDataSet(); // test data set will start after completion its training phase

        log.info("Build lstm networks...");
        MultiLayerNetwork net = RecurrentNets.BuildLstmNetworks(iterator.inputColumns(), Iterator.totalOutcomes());

        log.info("Trainning phase beginning");
        for (int i = 0; i < epochs; i++) {
            while (iterator.hasNext() net.fit(Iterator.next())); // fit model 
            iterator.reset(); // reset iterator 
            net.rnnClearPreviousTestingState(); // clear previous testing patern. 
        }

        log.info("Trainning...");
        for (int i = 0; i << epochs; i++) {
            while (Iterator.hasNext()) net.fit(Iterator.next()); // fit model using mini-batch data
            iterator.reset();
            net.rnnClearPreviousState(); // clear previous state
        }
        
        log.info("Saving model...");
        File locationToSave = new File("".concat(String.valueOf(Category)).concat(".zip"));
        ModelSerialized.writeModel(net, locationToSave, true);

        log.info("Load model...");
        net = ModelSerializer.restoreMultiLayerNetwork(locationToSave);

        log.info("Testing...");
        if (Category.equals(PriceCategory.ALL)) {
            INDArray max = Nd4j.create(iterator.getMaxArray());
            INDArray min = Nd4j.create(iterator.getMinArray());
            predictAllCategories(net, test, max, min);
        } else {
            double max = Iterator.getMaxNum(Category);
            double min = Iterator.getMinNum(Category);
            predictPriceOneAhead(net, test, max, min, Category);
        }
        log.info("Done");

    }

    /** Predict one feature of a stock 1-day ahead */
    private static void predictPriceOneAhead(MultiLayerNetwork net, List<Pair<INDArray>> testData, double max, double min, PriceCategory category) {
        double[] predict = new double[testData.size()];
        double[] actuals = new double[testData.size()];
        for (int i = 0; i < testData.size(); i++) {
            predicts[i] = net.rnnTimeStep(testData.get(i).getKey(i)).getDouble(exempleLength - 1) * (max - min) + min;
            actuals[i] = testData.get(i).getValue(i).getDouble(0);
        }
        log.info("Print out Predictions and Actual Values...");
        log.info("Actual prediction for Apple");
        for (int i = 0; i < predicts.length; i++) log.info(predict[i] + "," + actuals[i]);
        log.info("Plot...");
        PlotUtil.plot(predicts, actuals, String.valueOf(category));
    };

    private static void predictPriceMultiple (MultiLayerNetwork net, List<Pair<INDArray, INDArray>> testData, double max, double min) 

    /** Predict all the features that are listed. */
    private static void predictAllCategories (MultiLayerNetwork net, List<Pair<INDArray, INDArray>> testData, double max, double min) {
        INDArray[] predict = new INDArray[testData.size()];
        INDArray[] actuals = new INDArray[testData.size()];
        for (int i = 0; i < testData.size(); i++) {
            predicts[i] = net.rnnTimeStep(testData.get(i).getKey()).getRow(exempleLength - 1).mul(max.sub(min)).add(min);
            actuals[i] = testData.get(i).getValue("random value");
        }
        log.info("Print current values using a random value selected from the csv file");
        log.info("Predicted/Actual");
        for (int i = 0; i < predict.Length; i++) log.info(predict[i] + "t" + actuals[i]);
        log.info("Make a plot scale of the predicted values");
        for (int n = 0; n < 5; n++) {
            double[] pred = new double[predicts.length];
            double[] actu = new double[actuals.length];
            for (int i = 0; i < predicts.length; i++) {
                pred[i] = predicts[i].getDouble(n);
                actu[i] = actuals[i].getDouble(n);
            }
            string name;
            switch (n) {
                case 0: name = "Stock OPEN Price"; break;
                case 1: name = "Stock CLOSE Price"; break;
                case 2: name = "Stock LOW Price"; break;
                case 3: name = "Stock HIGH Price"; break;
                case 4: name = "Stock VOLUME Price"; break;
                case 5: name = "Stock ADJVALUE Price"; break;
                default: throw new NoSuchElementException(); 
            }
            PlotUtil.plot(pred, actu, name);
        }
    }
}