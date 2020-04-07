# AUTHOR: Daniel Raymond
# DATE  : 2020-04-06
# ABOUT : Hand-done multiplication using numpy to remove tensorflow from project (except for dataset)

import tensorflow as tf
import numpy as np
from weights import weights, biases

# STRUCTURE - LAYER : NODE : WEIGHT TO PREVIOUS LAYER INDEX
# print(weights[0][0][0])

mnist = tf.keras.datasets.mnist
(x_train, y_train), (x_test, y_test) = mnist.load_data()

