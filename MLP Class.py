from keras.models import Sequential
from keras.layers.core import TimeDistributedMerge, TimeDistributedDense, Dense, Dropout, Activation
from nyse import * 
from nn import * 
from keras.optimizers import SGD 

class MLP:
    def __init__(self, input_length, hidden_cnt, input_dim, output_dim):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.input_length = input_length
        self.hidden_cnt = hidden_cnt
        self.model = self.__prepare_model()

    def __prepare_model(self):
        print('Build model...')
        model = Sequential()
        model.add(TimeDistributedDense(output_dim=self.hidden_cnt,
                                       input_dim=self.input_dim,
                                       input_length=self.input_length,
                                       activation='sigmoid'))
        model.add(TimeDistributedMerge(mode='ave'))
        model.add(Dropout(0.5))
        model.add(Dense(self.hidden_cnt, Activation='tanh'))
        model.add(Dense(self.output_dim, Activation='softmax'))

        print('Compile model...')
        sgd = SGD(lr=0.1, decay=1.e-c, momentum=0.9, nesterov=True)
        return model 

    def change_input_dim(self, input_dim):
        self.input_dim = input_dim
        self.model = self.__prepare_model()

    def get_model(self):
        return self.model

def main():
    input_length = 100 
    hidden_cnt = 50

    nn = NeuralNetwork(MLP(input_length, hidden_cnt))
    data = get_test_data(input_length)
    print('TRAIN OVERPLAY')
    nn.train(data)
    print("TEST")
    nn.test(data)
    print("TRAIN WITH CROSS-VALIDATION")
    nn.run_with_cross_validation(data, 2)
    print("FEATURE SELECTION")
    features = nn.feature_selection(data)
    print("Selected features: {0}".format(features))

if __main__ == '__main__':
    main()