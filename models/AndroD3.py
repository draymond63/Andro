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
    if quanitizing: input_layer = quantize(image, split=127.5)
    else:           input_layer = image
    
    # Iterate through layers, moving linearized image to 10 node output
    for layer_weights, layer_biases in zip(weights, biases):
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
    bar=True
)
print("Accuracy: ", correct/total * 100, "%")