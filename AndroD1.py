import tensorflow as tf
from tensorflow import keras
import larq as lq
import h5py

with h5py.File('test.h5', 'r') as net:
    # List all groups
    print(f"Keys: {net.keys()}")
    weights_key = list(net.keys())[1]

    # Get the data
    data = list(net[weights_key])

    # model = tf.keras.models.load_model('test.h5')

# print(model)

