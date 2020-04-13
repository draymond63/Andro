# AUTHOR: Daniel Raymond
# DATE  : 2020-04-011
# ABOUT : Packing bits into bytes to more closely resemble hardware

import os
import sys
src_path = 'c:\\Users\\dan\\Desktop\\Projects\\Andro\\models\\src'
sys.path.append(src_path)

# Supress Tensorflow dll warning
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from weights_transpose import weights, biases, mnist # ! VSCode Error is incorrect -> Doesn't check sys.path
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
from tqdm import tqdm

file_name = 'data_packed'

# * 0's are treated as -1
def scale(num):
    if num >= 0: return 1
    else:        return 0 

def save_image(m, file):
    img = m.reshape([1, -1]).tolist()[0]
    
    file.write("(")
    for i1 in range(0, len(img), 8):
        # Pack bits into byte
        if i1 != 0:
            file.write(", ")
        file.write("0b")
        # 8, until there isn't enough for 8, then just do the rest
        max_length = min(len(img[i1:]), 8)
        # Loop through weights in reverse packs of 8 to flip endianness
        for i2 in range(max_length - 1, -1, -1):
            weight = img[i1 + i2]
            weight = weight / 127.5 - 1 # Scale to be between -1 and 1
            file.write(f"{scale(weight)}")
    file.write("),\n")

# Save mnist data easily
def save_mnist(name, data, file, scale):
    # Create a list of the object
    file.write(f"{name} = (")
    # Iterate through each variable
    for index in data:
        if scale:
            save_image(index, file)
        else:
            file.write(f"{index},")
    file.write(")\n\n")

# Save all useful constants in a single file
def scale_data(name, inc_mnist=True, inc_weights=True, inc_biases=True, inc_shape=True, mnist_len=10000):
    with open(f'{src_path}\\{name}.py', 'w') as file:
        # * Mnist data
        if inc_mnist:
            print("Saving mnist data")
            x_test, y_test = mnist[1]
            # save_mnist("x_train", x_train[], file, scale=True)
            # save_mnist("y_train", y_train, file, scale=False)
            save_mnist("x_test", x_test[:mnist_len], file, scale=True)
            save_mnist("y_test", y_test[:mnist_len], file, scale=False)

        # * Weights & Biases
        if inc_weights:
            print("Saving weights")
            file.write("weights = (\n")
            for layer in weights:
                file.write("### LAYER\n(\n")
                for x, node in enumerate(layer):
                    file.write("(")
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

                    file.write(f"), # Node {x}\n") # Pack all weights for a node into an list
                file.write("),\n") # Pack all node packages into a matrix (list of lists)
            file.write(")\n") # Pack all matrices into a list of layers

        # * Weights & Biases
        if inc_biases:
            print("Saving Biases")
            file.write("biases = (\n")
            for layer_biases in biases:
                file.write("(")
                for bias in layer_biases:
                    file.write(f"{bias}, ")
                file.write("),\n") # Pack all biases into a layer
            file.write(")\n") # Pack all matrices into a list of layers
        
        if inc_shape:
            print("Saving Shape")
            file.write("shape = (784, ") # Input size is 784 pixels
            for layer in weights:
                file.write(f"{len(layer)}")
                if layer != weights[-1]: # If it's the last layer, don't print the comma
                    file.write(", ")

            file.write(")\n")


if __name__ == "__main__":
    print("Packing mnist, weights, and biases")
    scale_data(file_name, mnist_len=50)
    print("Packing succcessful")
