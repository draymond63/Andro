import tensorflow as tf
from tensorflow import keras
import larq as lq
import h5py

with h5py.File('test.h5', 'r') as f:
    # List all groups
    print(f"Keys: {f.keys()}")
    a_group_key = list(f.keys())[0]

    # Get the data
    data = list(f[a_group_key])

for i in data:
    print(f"{i}:\t{data}")