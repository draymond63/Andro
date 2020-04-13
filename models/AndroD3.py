# AUTHOR: Daniel Raymond
# DATE  : 2020-04-07
# ABOUT : Hand-done multiplication to remove numpy from the project (About 1124x slower than D0, 3 img/s with quantization, 20 img/s w/o)

# Supress Tensorflow dll warning
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from src.weights_transpose import weights, biases, mnist
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
from tqdm import tqdm

# * STRUCTURE OF WEIGHTS - LAYER : NODE : WEIGHT TO PREVIOUS LAYER

(x_train, y_train), (x_test, y_test) = mnist

# * NOT USED ANYMORE - Changed model to move away from linear algebra to more node-like thinking
# Needs weights, not weights_transpose
def matmul(m1, m2):
    # * USAGE -> layer = matmul(input_layer, layer_weights)
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

def quantize(a, split=0):
    if type(a) is list:
        new = [] # New list same length as a
        for x in a:
            if x >= split:  new.append(1)
            else:           new.append(-1)
        return new
    else:
        if a >= split:  return 1
        else:           return -1

# Functional model that takes in an image and guesses the number (mnist)
def model(image, quanitizing=False, inc_biases=False):
    # Quantize incoming image if required
    if quanitizing: input_layer = quantize(image, split=127)
    else:           input_layer = image
    
    # Iterate through layers, moving linearized image to 10 node output
    for layer_weights, layer_biases in zip(weights, biases):
        print(input_layer)
        output_layer = []
        # Iterate through each of the nodes in the current layer
        for node_weights, node_bias in zip(layer_weights, layer_biases):
            assert len(input_layer) == len(node_weights), f"Weights do not correspond to nodes in the previous layer - {len(input_layer)} : {len(node_weights)}"
            node_val = 0
            # Iterate through previous layer, multiplying previous nodes by the weights and putting it into the new node
            for data, weight in zip(input_layer, node_weights):
                # Take the MSB of the val if required
                if quanitizing: node_val += quantize(weight) * quantize(data)
                else:           node_val += weight * data
            # Add bias
            if inc_biases:
                node_val += node_bias
            # Add value to new layer
            output_layer.append(node_val)
        # Current layer becomes the input for the next one
        input_layer = output_layer
        # Quantize all input layers if required
        if quanitizing:
            input_layer = quantize(input_layer)

    # Return actual guess instead of encoded logits vector
    print(output_layer)
    answer = output_layer[0] # Start off guessing it is zero
    index = 0
    for i, challenger in enumerate(output_layer):
        if challenger >= answer:
            answer = challenger
            index = i

    return index

def test_model(images, answers, quanitizing=False, inc_biases=False, bar=True):
    correct = 0
    incorrect = 0
    # Add progress bar unless specified otherwise
    if bar:
        pbar = tqdm(total=len(answers))
    # Iterate through every image given
    for image, answer in zip(images, answers):
        # Flatten image for model
        img = image.reshape([1, -1]).tolist()[0]
        # Update progress bar
        if bar:
            pbar.update(n=1)
        # Use model to make a prediction
        guess = model(img, quanitizing, inc_biases)
        # print(guess)
        # Evaluate
        if guess == answer:
            correct += 1
        else:
            incorrect += 1
    if bar:
        pbar.close()
    return (correct, incorrect, len(images))

length = 1 # max of 10000
print(f"Testing model with {length} image{'s' if length != 1 else ''}")
correct, incorrect, total = test_model(
    x_test[:length], 
    y_test[:length], 
    quanitizing=True, 
    inc_biases=False,
    bar=False
)
print("Accuracy: ", correct/total * 100, "%")