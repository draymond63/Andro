# AUTHOR: Daniel Raymond
# DATE  : 2020-04-011
# ABOUT : Packing bits into bytes to more closely resemble hardware

import os
import sys
sys.path.append('c:\\Users\\dan\\Desktop\\Projects\\Andro\\src')

# Supress Tensorflow dll warning
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from weights_transpose import weights, biases, mnist
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'

file_name = 'data_packed'

# * 0's are treated as -1
def scale(num):
    if num >= 0: return 1
    else:        return 0 

def scale_matrix(m):
    # Create matrix with the correct dimensions
    result = [
        [0]*len(m[0]) 
        for _ in range(len(m)) 
    ]
    # File matrix with scaled values
    for x, row in enumerate(m):
        for y, element in enumerate(row):
            result[x][y] = scale(element)
    # Return result
    return result

# Save mnist data easily
def save_list(name, data, file, scale):
    # Create a list of the object
    file.write(f"{name} = [\n")
    # Iterate through each variable
    for index in data:
        if scale:
            file.write(f"{scale_matrix(index)}, \n")
        else:
            file.write(f"{index}, \n")
    file.write("]\n\n")

# Save all useful constants in a single file
def scale_data(name):
    with open(f'{name}.py', 'w') as file:
        # * Mnist data
        # (x_train, y_train), (x_test, y_test) = mnist
        # save_list("x_train", x_train, file, scale=True)
        # save_list("y_train", y_train, file, scale=False)
        # save_list("x_test", x_test, file, scale=True)
        # save_list("y_test", y_test, file, scale=False)

        # * Weights & Biases
        file.write("weights = [\n")
        for layer in weights:
            file.write("### LAYER\n[\n")
            for x, node in enumerate(layer):
                file.write("[")
                for i1 in range(0, len(node), 8):
                    # Pack bits into byte
                    if i1 != 0:
                        file.write(", ")
                    file.write("0b")
                    # 8, until there isn't enough for 8, then just do the rest
                    max_length = min(len(node[i1:]), 8)
                    # Loop through weights in reverse packs of 8 to flip endianness
                    for i2 in range(max_length - 1, -1, -1):
                        weight = node[i1 + i2]
                        file.write(f"{scale(weight)}")

                file.write(f"], # Node {x}\n") # Pack all weights for a node into an list
            file.write("],\n") # Pack all node packages into a matrix (list of lists)
        file.write("]\n") # Pack all matrices into a list of layers

scale_data(file_name)
