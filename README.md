# Andro
A deconstruction of a Binarized Neural Network (BNN) to eventually implement in hardware.

## Models
The models are organized as a way of deconstructing the Neural Network as a way of boiling 
down the Tensorflow into something that can be used by a circuit. Each model is labeled as
'AndroDX.py", where X is the iteration: how far removed it is from TF. 

### D0
Creates and trains the intial Neural Network using Keras and Larq. 
### D1
Proves that the weights saved by D0 can be re-read and used by a Keras model.
### D2
Removes Tensorflow by handling all data with pure numpy.
### D3
Removes numpy by treating doing multiplication by hand, thinking about NN as layers rather than
a series of matrices.
### D4
Uses packed weights to 
### D5
Uses sim directory to emulate the circuit as closely as possible

## Source (src)
This directory the shape and data required for the models to function. This includes weights,
biases, input data, and all of their packed versions.

## Tools
These manipulate data permanently and interface with Arduino to actually use the circuit. 