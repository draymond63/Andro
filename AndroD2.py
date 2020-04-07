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

def model(image):
    layer = [image]
    for i in range(len(weights)):
        layer_weights = np.array(weights[i], dtype=np.float32)
        layer.append(np.matmul(layer[-1], layer_weights))

    # Return actual guess instead of encoded probability vector
    answer = layer[-1][0][0] # Start off guessing it is zero
    index = 0
    for i, challenger in enumerate(layer[-1][0]):
        if challenger >= answer:
            answer = challenger
            index = i

    # return index
    return index

def test_model(images, answers):
    correct = 0
    incorrect = 0
    for image, answer in zip(images, answers):
        # Flatten image for model
        img = image.reshape([1, -1])
        # Use model to make a prediction
        guess = model(img)
        # Evaluate
        if guess == answer:
            correct += 1
        else:
            incorrect += 1
    
    return (correct, incorrect, len(images))

print("Starting model")
correct, incorrect, total = test_model(x_test, y_test)
print(correct/total * 100, "%")