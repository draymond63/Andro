# AUTHOR: Daniel Raymond
# DATE  : 2020-04-06
# ABOUT : Proves weights & biases file works by creating a keras model that uses them

import os
import sys
sys.path.append('c:\\Users\\dan\\Desktop\\Projects\\Andro\\src')

# Supress Tensorflow dll warning
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
import numpy as np
from weights import weights, biases, mnist

# * STRUCTURE OF WEIGHTS - LAYER : NODE : WEIGHT TO PREVIOUS LAYER

(x_train, y_train), (x_test, y_test) = mnist


# Make and load new model
model = tf.keras.models.Sequential([
    tf.keras.layers.Dense(512, 
        input_shape=(784,)
    ),
    tf.keras.layers.Dense(10, 
        activation="softmax"
    )
])
for i, layer in enumerate(model.layers):
    temp_weights = np.asarray(weights[i], dtype=np.float32)
    temp_biases = np.asarray(biases[i], dtype=np.float32)

    # Polarize every weight
    for x, node in enumerate(temp_weights):
        for y, weight in enumerate(node):
            if weight > 0:
                temp_weights[x][y] = 1
            else:
                temp_weights[x][y] = -1

    temp = [temp_weights, temp_biases]
    layer.set_weights(temp)
# Create new model with Flatten layer in front
model = tf.keras.models.Sequential([
    tf.keras.layers.Flatten(),
    model.layers[0],
    model.layers[1]
])

# Testing model to see that weights were stored properly
model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

test_loss1, test_acc1 = model.evaluate(x_train, y_train, verbose=0)
test_loss2, test_acc2 = model.evaluate(x_test, y_test, verbose=0)

test_acc = (test_acc1 * len(x_train) + test_acc2 * len(x_test)) / (len(x_train) + len(x_test))

print(f"Test accuracy {test_acc * 100:.2f} %")