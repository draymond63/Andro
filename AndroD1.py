# AUTHOR: Daniel Raymond
# DATE  : 2020-04-06
# ABOUT : Proves weights & biases file works by creating a keras model that uses them

import tensorflow as tf
import numpy as np
from weights import weights, biases

# STRUCTURE - LAYER : NODE : WEIGHT TO PREVIOUS LAYER INDEX
# print(weights[0][0][0])

mnist = tf.keras.datasets.mnist
(x_train, y_train), (x_test, y_test) = mnist.load_data()


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
    tf.print(layer)
    temp_weights = np.asarray(weights[i], dtype=np.float32)
    temp_biases = np.asarray(biases[i], dtype=np.float32)

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

test_loss, test_acc = model.evaluate(x_train, y_train)
print(f"Test accuracy {test_acc * 100:.2f} %")