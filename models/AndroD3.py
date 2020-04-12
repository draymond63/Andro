# AUTHOR: Daniel Raymond
# DATE  : 2020-04-07
# ABOUT : Hand-done multiplication to remove numpy from the project

import os
import sys
sys.path.append('c:\\Users\\dan\\Desktop\\Projects\\Andro\\src')

# Supress Tensorflow dll warning
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from weights import weights, biases, mnist
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
from tqdm import tqdm

# * STRUCTURE OF WEIGHTS - LAYER : NODE : WEIGHT TO PREVIOUS LAYER
# print(weights[0][0][0])

(x_train, y_train), (x_test, y_test) = mnist

def matmul(m1, m2):
    # Gather dimension data of both matrices
    m1_dim = (len(m1), len(m1[0]))
    m2_dim = (len(m2), len(m2[0]))
    result_dim = (m1_dim[0], m2_dim[1])
    # print(result_dim)
    assert m1_dim[1] == m2_dim[0], 'Inner dimensions must remain consistent when multiplying matrices'
    inner_dim = m1_dim[1]

    result = [ # Create matrix with the correct dimensions
        [0]*result_dim[1] 
        for _ in range(result_dim[0]) 
    ]

    # Iterate through each element in the resultant matrix
    for row in range(result_dim[0]):
        for col in range(result_dim[1]):
            # Iterate through each row and column, multiplying and adding (Per node)
            for i in range(inner_dim):
                result[row][col] += m1[row][i] * m2[i][col] # Each node

    return result

def model(image):
    layer = image
    for layer_weights, layer_biases in zip(weights, biases):
        layer = matmul(layer, layer_weights)

    # Return actual guess instead of encoded logits vector
    answer = layer[0][0] # Start off guessing it is zero
    index = 0
    for i, challenger in enumerate(layer[0]):
        if challenger >= answer:
            answer = challenger
            index = i

    # return index
    return index

def test_model(images, answers):
    correct = 0
    incorrect = 0
    pbar = tqdm(total=len(answers))
    for image, answer in zip(images, answers):
        # Flatten image for model
        img = image.reshape([1, -1]).tolist()
        # Update progress bar
        pbar.update(n=1)
        # Use model to make a prediction
        guess = model(img)
        # print(guess)
        # Evaluate
        if guess == answer:
            correct += 1
        else:
            incorrect += 1
    pbar.close()
    return (correct, incorrect, len(images))

length = 10
print(f"Testing model with {length} image{'s' if length != 1 else ''}")
correct, incorrect, total = test_model(x_test[:length], y_test[:length])
print(correct/total * 100, "%")