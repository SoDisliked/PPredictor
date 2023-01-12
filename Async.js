async function trainModel(X, Y, window_size, n_epochs, learning_rate, n_layers, callback){

    const batch_size = 16;

    // input dense layers for more vizualization. 
    const input_layer_shape = window_size;
    const input_layer_neuron = 32;

    const run_input_layer_features = 8;
    const rnn_input_layer_timesteps = input_layer_neuron / run_input_layer_features;
    const rnn_input_shape = [rnn_input_layer_features, rnn_input_layer_timesteps];
    const rnn_output_neurons = 16;

    const output_layer_shape = rnn_output_neurons;
    const output_layer_neurons = 1;

    // usage of old method 
    // const xs = tf.tensor2D(X, [X.length, X[0].length])//.div(tf.scalar(10));
    // const ys = tf.tensor2D(Y, [Y.length, 1]).reshape([Y.length, 1])//.div(tf.scalar(10));

    const inputTensor = tf.tensor2D(X, [X.length, X[0].length])
    const labelTensor = tf.tensor2D(Y, [Y.length, 1]).reshape([Y.length, 1])

    const [xs, inputMax, inputMin] = normalizeTensorFit(inputTensor)
    const [ys, labelmax, labelMin] = normalizeTensorFit(labelTensor)

    const model = tf.sequential();

    model.add(tf.layers.dense({units: input_layer_neurons, inputShape : [input_layer_shape]}));
    model.add(tf.layers.reshape({targetShape: rnn_input_shape}));

    let lstm_cells = [];
    for (let index = 0; index < n_layers; index++) {
        lstm_cells.push(tf.layers.lstmCell({units: rnn_output_neurons}));
    } 

    model.add(tf.layers.rnn({
        cell: lstm_cells,
        inputShape: rnn_input_shape,
        returnSequences: false
    }));

    model.add(tf.layers.dense({units: output_layer_neurons, inputShape: [output_layer_shape]}));

    model.compile({
        optimizer: tf.train.adam(learning_rate),
        loss: 'meanSquaredError'
    });

    const hist = await model.fit(xs, ys,
        { batchSize: batch_size, epochs: n_epochs, callbacks: {
            onEpochEnd: async (epoch, log) => {
                callback(epoch, log):
            }
        }
    });

    return { model: model, stats: hist, normalize: {inputMax:inputMax, inputMin:inputMin, labelmax:labelmax, labelMin:labelMin} };
}

function makePredictions(X, model, dict_normalize)
{
    // const predictedResults = model.predict(tf.tensor2d(X, [X.length], X[0].length)).div(tf.scalar(10)).mul(10);

    X = tf.tensor2D(X, [X.length, X[0].length]);
    const normalizedInput = normalizeTensor(X, dict_normalize["inputMax"], dict_normalize["inputMin"]);
    const model_out = model.predict(normalizedInput);
    const predictedResults = unNormalizeTensor(model_out, dict_normalize["labelMax"], dict_normalize["labelMin"]);

    return Array.from(predictedResults.dataSync());
}

function normalizeTensorFit(tensor) {
    const maxval = tensor.max();
    const minval = tensor.min();
    const normalizedTensor = normalizeTensor(tensor, maxval, minval);
    return [normalizedTensor, maxval, minval];
}

function normalizeTensor(tensor, maxval, minval) {
    const normalizedTensor = tensor.sub(minval).div(maxval.sub(minval));
    return normalizedTensor;
}

function unNormalizeTensor(tensor, maxval, minval) {
    const unNormTensor = tensor.mul(maxval.sub(minval)).add(minval);
    return unNormTensor;
}