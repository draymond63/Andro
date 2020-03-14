import tensorflow as tf
import larq as lq

# Training data
mnist = tf.keras.datasets.mnist
(x_train, y_train), (x_test, y_test) = mnist.load_data()

# print(x_train[0]) # One image

# Reshape data for CNN (images, height, width, channels)
x_train = x_train.reshape((60000, 28, 28, 1))
x_test = x_test.reshape((10000, 28, 28, 1))

# Normalize input to be between [-1, 1]
x_train = x_train / 127.5 - 1
x_test = x_test / 127.5 - 1

# Default for most layers
kwargs = dict(input_quantizer="ste_sign",
              kernel_quantizer="ste_sign",
              kernel_constraint="weight_clip",
              use_bias=False)

# Creating the full model
model = tf.keras.models.Sequential()

# Add a quantixed convalutional neural network (3x3 kernel on 28x28 1 channel image)
# Quantized according to ste_sign -> outerbound(-1, 1), no bias added after
model.add(lq.layers.QuantConv2D(32, (3, 3),
                                kernel_quantizer="ste_sign",
                                kernel_constraint="weight_clip",
                                use_bias=False,
                                input_shape=(28, 28, 1)))

# Display a summer of the model's layers
lq.models.summary(model)

# # Compile model XXX EXPLAIN?
# model.compile(optimizer='adam',
#               loss='sparse_categorical_crossentropy',
#               metrics=['accuracy'])

# # Train the NN
# model.fit(x_train, y_train, batch_size=64, epochs=6)

# # See how accurate the NN is
# test_loss, test_acc = model.evaluate(x_test, y_test)
# print(f"Test accuracy {test_acc * 100:.2f} %")