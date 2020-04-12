# AUTHOR: Daniel Raymond
# DATE  : 2020-04-06
# ABOUT : Hand-done multiplication using numpy to remove tensorflow from project

import os
import sys
sys.path.append('c:\\Users\\dan\\Desktop\\Projects\\Andro\\src')

# Supress Tensorflow dll warning
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from weights import weights, biases, mnist
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
import numpy as np
from tqdm import tqdm

# * STRUCTURE OF WEIGHTS - LAYER : NODE : WEIGHT TO PREVIOUS LAYER

(x_train, y_train), (x_test, y_test) = mnist

# ! Quantizing makes it shit the bed (So it's definitely wrong)
def quantize(layer):
    # mapElement = lambda x: 1 if x >= 0 else -1
    # vfunc = np.vectorize(mapElement)
    
    # return vfunc(layer) # Convert each layer to -1 or 1
    return layer

def model(image, use_biases=True):
    layer = quantize(image)
    for layer_weights, layer_biases in zip(weights, biases):
        layer_weights = np.array(layer_weights, dtype=np.float32)
        # Stil 78.72% accuracy without biases? (Same as with)
        if use_biases: 
            layer_biases = np.array(layer_biases, dtype=np.float32)
        else:
            layer_biases = 0
        layer = np.matmul(layer, layer_weights) + layer_biases
        # Quantize all but the last layer
        if len(layer[0]) != 10:
            layer = quantize(layer)

    # Return actual guess instead of encoded logits vector
    answer = layer[0][0] # Start off guessing it is zero
    index = 0
    for i, challenger in enumerate(layer[0]):
        if challenger >= answer:
            answer = challenger
            index = i

    # return index
    return index

def test_model(images, answers, use_biases=True):
    correct = 0
    incorrect = 0
    pbar = tqdm(total=len(answers))
    for image, answer in zip(images, answers):
        # Flatten image for model
        img = image.reshape([1, -1])
        # * Use model to make a prediction
        guess = model(img, use_biases)
        pbar.update(n=1)
        # Evaluate
        if guess == answer:
            correct += 1
        else:
            incorrect += 1
    pbar.close()
    return (correct, incorrect, correct + incorrect)

length = 1000
print(f"Testing model with {length} image{'s' if length != 1 else ''}")
correct, incorrect, total = test_model(x_test[:length], y_test[:length])
print(correct/total * 100, "%")
