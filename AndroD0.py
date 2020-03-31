import tensorflow as tf
import numpy as np
from tqdm import tqdm

mnist = tf.keras.datasets.mnist
(x_train, y_train), (x_test, y_test) = mnist.load_data()


num_epochs = 1
train_length = 5 # How many images per epoch to train with (MAX 60000)
x_train, y_train = x_train[:train_length,], y_train[:train_length,]

# Dense layer scruture
def dense(inputs , weights):
    dropout_rate = 0.1
    leaky_relu_alpha = 0.2

    x = tf.nn.leaky_relu( tf.matmul(inputs, weights) , alpha=leaky_relu_alpha )
    return tf.nn.dropout( x , rate=dropout_rate )

# Initialize all weights to random stuff
initializer = tf.initializers.glorot_uniform()
def get_weight(shape , name):
    return tf.Variable( initializer(shape) , name=name , trainable=True , dtype=tf.float32 )

# Size of each dense layer
i_size = 28*28
o_size = 10
shapes = [
    [i_size, 3600],
    [3600,   2400],
    [2400,   1600],
    [1600,   800],
    [800,    64],
    [64,     o_size]
]

weights = []
for i in range( len( shapes ) ):
    weights.append( get_weight( shapes[i] , f'layer {i}') )

def model(x) :
    x = tf.cast( x, dtype=tf.float32 ) # bits for input?
    for i in range(len(shapes)):
        x = dense(x, weights[i])
    return x

def loss(pred, target):
    return tf.losses.categorical_crossentropy(target, pred)

optimizer = tf.keras.optimizers.SGD( learning_rate=0.1 )

def train_step(current_model, inputs, expected):
    with tf.GradientTape() as tape:
        current_loss = loss(current_model(inputs), expected)
    grads = tape.gradient(current_loss, weights)

    temps = weights # Store weights temporarily
    optimizer.apply_gradients(zip(grads, weights))

    # Check to see if gradient was applied
    for temp, weight in zip(temps, weights):
        if (not np.any(weight.numpy() - temp.numpy())):
            print(f"{weight.name} did not change")
    return float(tf.reduce_mean(current_loss))
    

for e in range(num_epochs):
    losses = []
    # pbar = tqdm(total=len(x_train))
    # Iterate through each image in x_train
    for x, y in zip(x_train, y_train):
        x = x.reshape([1, -1]) # Flatten input matrix to be linear
        y = tf.one_hot(y, depth=10) # Number of answers is depth of vector

        losses.append( train_step(model, x, y) )  # Train the step and update the losses
        # print( f"{np.mean(losses)}\t{losses[-1]}" )
        # pbar.update(1)

    # pbar.close()
