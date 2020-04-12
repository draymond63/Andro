#!/usr/bin/python3
import time
import numpy as np
from sklearn.datasets import fetch_openml, load_digits
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split

class Neural_Net(object):
    def __init__(self, x_train, y_train, x_test, y_test, num_hidden, num_epochs, learning_rate, epsilon, beta):
        '''
          A neural network object that uses one hidden layer (with num_hidden hidden nodes), sigmoid output functions at each layer
          and gradient descent learning to minimize the MSE loss.
         ...
        Parameters
        ----------
        :param x_train:         input matrix of size (m,n) where m is the number of objects that were classified, and n is the dimension of each object.
        :param y_train:         "class label matrix of size (m,x) where m is the number of objects that were classified, and x are the number of classes an object can take on."
        :param num_hidden:      The number of hidden layer nodes.
        :param num_epochs:      The epochs that will be used to learn the training data.
        :param learning_rate:   The amount we nudge the weights in the direction of the error gradient.
        :param epsilon:         The threshold for which we set an error to be 0.

        :type X:                ndarray
        :type Y:                ndarray
        :type num_hidden:       int
        :type learning_rate:    float
        :type epsilon:          float

        :return: The output delta (output error * derivative of activation), and hidden delta (output error propogagted back * derivative of activation)
        '''
        super().__init__()
        self.num_outputs = y_train.shape[1]
        self.num_inputs = x_train.shape[1]
        self.num_hidden = num_hidden
        self.num_epochs = num_epochs
        self.learning_rate = learning_rate
        self.epsilon = epsilon
        self.beta = beta
        self.hidden_weights = np.random.randn(
            self.num_inputs, self.num_hidden)*0.001
        self.output_weights = np.random.randn(
            self.num_hidden, self.num_outputs)*0.001
        start = time.time()
        self.train(x_train, y_train, x_test, y_test)
        end = time.time()

        self.calc_metrics(x_train, y_train,"Training Set")
        print("////")
        self.calc_metrics(x_test, y_test,"Test Set")
        print("Training took {:.2f} minutes".format((end-start)/60))

    def train(self, x_train, y_train, x_test=None, y_test=None):
        """
            Iteratively feeds data through the network and then uses gradient descent to
            minimize loss. 

             Parameters
            ----------
            :param x_train: input matrix of size (m,n) where m is the number of objects that were classified, and n is the dimension of each object.
            :param y_train: class label matrix of size (m,x) where m is the number of objects that were classified, and x are the number of classes an object can take on."
            :param x_test:  A sample of the data set saved for validation.
            :param x_test:  Corresponding class labels.
            :type x_train: ndarray
            :type y_train: ndarray
            :type x_train: ndarray
            :type Y: ndarray


        """
        num_epochs = self.num_epochs
        # keep track of the previous weight changes for momentum
        prev_output_change = np.zeros((self.num_hidden, self.num_outputs))
        prev_hidden_change = np.zeros((self.num_inputs, self.num_hidden))
        for epoch in range(num_epochs):
            forwards_pass = self.forward_pass(x_train)
            gradients = self.backwards_pass(x_train, y_train, forwards_pass)
            output_change, hidden_change = gradients['output_change'], gradients['hidden_change']
            # Add momemntum: new weight change = calculated change from gradient descent +
            output_change = output_change+(self.beta*prev_output_change)
            hidden_change = hidden_change+(self.beta*prev_hidden_change)
            # I found it helpful to scale the weight changes by the size of the training set
            self.output_weights -= (1./len(x_train)) * output_change
            self.hidden_weights -= (1./len(x_train)) * hidden_change
            if epoch == 0 or num_epochs < 10 or (epoch+1) % (num_epochs//10) == 0:
                y_hat = self.forward_pass(x_train)
                loss = self.MSE_loss(y_train, y_hat['y_output'])
                print("Epoch {}: \t MSE \t\t= {}".format(epoch+1, loss))
                if not x_test is None:
                    y_hat = self.forward_pass(x_test)
                    loss = self.MSE_loss(y_test, y_hat['y_output'])
                    if loss < 0.01:
                        break
                    print("\t\t Test MSE \t= {}".format(loss))
                print("Any change to output weights? {}".format(
                    not np.all(output_change == 0)))
                print("Any change to hidden weights? {}".format(
                    not np.all(hidden_change == 0)))

    def forward_pass(self, X):
        """
            Performs the weighted sum with activation function (both layers use sigmoid) for the entire data set using Numpy's 
            provided matrix multiplication function.
        """ 
        hidden_weights = self.hidden_weights
        output_weights = self.output_weights
        feed_forward = {}
        feed_forward['a_hidden'] = np.matmul(X, hidden_weights)
        feed_forward['y_hidden'] = self._sigmoid(feed_forward['a_hidden'])
        feed_forward['a_output'] = np.matmul(
            feed_forward['y_hidden'], output_weights)
        feed_forward['y_output'] = self._sigmoid(feed_forward['a_output'])
        return feed_forward

    def backwards_pass(self, X, Y, forwards_pass):
        """
            Performs gradient descent learning given an input matrix of size mXn, class labels of mXx
            and the 
         ...
        Parameters
        ----------
        :param X: input matrix of size (m,n) where m is the number of objects that were classified, and n is the dimension of each object.
        :param Y: class label matrix of size (m,x) where m is the number of objects that were classified, and x are the number of classes an object can take on.
        :param forwards_pass: activation matrix of size (m,i), output matrix of size (m,i)
        :type X: ndarray
        :type Y: ndarray
        :type forward_pass: dict
        :return: The output delta (output error * derivative of activation), and hidden delta (output error propogagted back * derivative of activation)
        """
        def _threshold_error(error_arr):
            thresh_pos = error_arr < self.epsilon
            thresh_neg = error_arr > -self.epsilon
            error_arr[thresh_pos & thresh_neg] = 0
            return error_arr
        predictions = forwards_pass['y_output']
        learning_rate = self.learning_rate
        # error at output layer
        output_error = predictions-Y
        output_error = _threshold_error(output_error)
        output_delta = output_error * self._sigmoid_derivative(forwards_pass['a_output'])
        # The hidden layer just before the output has an error that is equal to the output delta * the transpose of the weights going from hidden->output
        hidden_error = np.matmul(output_delta, self.output_weights.T)
        hidden_delta = hidden_error * self._sigmoid_derivative(forwards_pass['a_hidden'])
        # The change of a particular layers weights is the previous layers activation (or the inputs) transposed
        # * the delta of that particular layer * the learning rate
        output_change = np.matmul(
            forwards_pass['y_hidden'].T, output_delta)*learning_rate
        hidden_change = np.matmul(X.T, hidden_delta)*learning_rate
        return {"output_change": output_change, "hidden_change": hidden_change}

    def _sigmoid_derivative(self, signal):
        # We limit the max and min values of our signal so that the sigmoid function doesn't overflow
        signal = np.clip(signal, -500, 500)
        return self._sigmoid(signal)*(1.-self._sigmoid(signal))

    def _sigmoid(self, signal):
        # We limit the max and min values of our signal so that the sigmoid function doesn't overflow
        signal = np.clip(signal, -500, 500)
        return 1./(1.+np.exp(-signal))

    def MSE_loss(self, y, y_hat):
        return (np.square(y_hat - y)).mean(axis=None)

    def calc_metrics(self, X, Y,title):
        print("{} Confusion Matrix - (row-> predicted, column-> actual)".format(title))
        label_str = [i for i in range(self.num_outputs)]
        dashes = ['-' for i in range(self.num_outputs)]
        print('\t', end='')
        print(*label_str, sep="\t")
        print('\t', end='')
        print(*dashes, sep='\t')
        cm = self.confusion_matrix(X, Y)
        for index, row in enumerate(cm):
            print('{} |\t'.format(index), end='')
            print(*row, sep="\t")
        recall = np.diag(cm) / np.sum(cm, axis=1).tolist()
        recall = ['%.2f' % elem for elem in recall]
        precision = np.diag(cm) / np.sum(cm, axis=0).tolist()
        precision = ['%.4f' % elem for elem in precision]
        print()
        print("{} Recall".format(title))
        print(*label_str, sep="\t")
        print(*dashes, sep='\t')
        print(*recall, sep="\t")
        print("{} Precision".format(title))
        print(*label_str, sep="\t")
        print(*dashes, sep='\t')
        print(*precision, sep="\t")

    def confusion_matrix(self, X, Y):
        forward_pass = self.forward_pass(X)
        predicted = [np.argmax(prediction)
                     for prediction in forward_pass['y_output']]
        actual = [np.argmax(true) for true in Y]
        cm = confusion_matrix(actual, predicted)
        return cm


if __name__ == '__main__':
    # training set size
    training_size = 1000
    test_size = training_size//4 # this gives us an 80 20 split between the test and training data
    print('--- fetching ---')
    X, y = fetch_openml('mnist_784', version=1, return_X_y=True)
    print('--- done fetching ---')
    print('--- normalize ---')
    X = np.float64(X)
    X /= 255
    # Add extra bias factor so we don't have to train it differently (a constant of 1)
    print('--- adding bias ---')
    bias = np.ones((X.shape[0], 1))
    X = np.append(X, bias, axis=1)
    # One-hot encoding
    y_encoded = np.zeros((y.size, 10))
    y_encoded[np.arange(y.size), y.astype(int)] = 1
    x_train, x_test, y_train, y_test = train_test_split(
        X, y_encoded, train_size=training_size, test_size=test_size, shuffle=True)
    neural_net = Neural_Net(x_train, y_train, x_test, y_test, num_hidden=350,
                            num_epochs=3500, learning_rate=0.9, epsilon=0.01, beta=0.1)
