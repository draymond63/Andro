# AUTHOR: Daniel Raymond
# DATE  : 2020-03-27
# ABOUT : Creates the intial NN and prints out all the weights to be saved in an external file

import tensorflow as tf
from tensorflow import keras
import larq as lq
import os

print ("# Starting Andro NN")

# Training data
mnist = tf.keras.datasets.mnist
(x_train, y_train), (x_test, y_test) = mnist.load_data()

# Normalize input to be between [-1, 1]
x_train = x_train / 127.5 - 1
x_test = x_test / 127.5 - 1

# 81 kB required minimum
model = tf.keras.models.Sequential([
    tf.keras.layers.Flatten(),
    lq.layers.QuantDense(512,
        input_shape=(784,),
        input_quantizer="ste_sign", # SteHeaviside
        kernel_quantizer="ste_sign",
        kernel_constraint="weight_clip"
    ),
    lq.layers.QuantDense(10,
        input_quantizer="ste_sign",
        kernel_quantizer="ste_sign",
        kernel_constraint="weight_clip",
        activation="softmax"
    ),
])

# Create callback to store the NN after each epoch
saveNN = tf.keras.callbacks.ModelCheckpoint(
    "./test.h5", # Creates unparsable h5 file 
    monitor='accuracy', 
    verbose=0, 
    save_best_only=True,
    save_weights_only=False, 
    mode='auto', # Determine whether best is a min or a max depending on the monitored metric
    save_freq='epoch'
)

# Print the summary
model.build(x_train.shape)
# model.summary()

# Compile model - sets key parameters for model.fit
model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

print ("# Training NN")
# Train the NN
history = model.fit(x_train, y_train, 
    batch_size=64, 
    epochs=500,
    verbose=0
    # callbacks=[saveNN]
)

# for key in history.history: # Print possible metrics
#     print(key)

# Display a summer of the model's layers DOESNT WORK WITH DENSE LAYERS?
# lq.models.summary(model)

# See how accurate the NN is
test_loss, test_acc = model.evaluate(x_test, y_test, verbose=0)
print(f"# Test accuracy {test_acc * 100:.2f} %")


def save_weights(name):
    with open(name, 'w') as output:
        print(f"weights = [", file=output)
        for i, layer in enumerate(model.layers):
            if i: # Ignore first layer
                weights = layer.get_weights()
                weights = weights[0]
                print("# -------------------------------- LAYER", i, "------------------", file=output)
                print(weights.tolist(), ",", file=output)
        print("]\n", file=output)

        print(f"biases = [", file=output)
        for i, layer in enumerate(model.layers):
            if i: # Ignore first layer
                weights = layer.get_weights()
                biases = weights[1]
                print("# -------------------------------- LAYER", i, "------------------", file=output)
                print(biases.tolist(), ",", file=output)
        print("]", file=output)

# save_weights("test.py")


print(f"weights = [")
for i, layer in enumerate(model.layers):
    if i: # Ignore first layer
        weights = layer.get_weights()
        weights = weights[0]
        print("# -------------------------------- LAYER", i, "------------------")
        print(weights.tolist(), ",")
print("]\n")

print(f"biases = [")
for i, layer in enumerate(model.layers):
    if i: # Ignore first layer
        weights = layer.get_weights()
        biases = weights[1]
        print("# -------------------------------- LAYER", i, "------------------")
        print(biases.tolist(), ",")
print("]")



# Test on a single image

# model.save('./test2.h5')