# AUTHOR: Daniel Raymond
# DATE  : 2020-04-012
# ABOUT : Neural network using packed bits technique and bitwise operators

# Supress Tensorflow dll warning
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from src.data_packed import x_test, y_test, weights, shape
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
from tqdm import tqdm

# * STRUCTURE OF WEIGHTS - LAYER : NODE : WEIGHT TO PREVIOUS LAYER

def XNOR(a, b):
	if a == b:  return 1
	else:       return 0

def NOT(a):
	if a: 	return 0
	else: 	return 1

def UpDown(value, direction):
	if direction == 1:
		return value + 1
	elif direction == 0:
		return value - 1

def getMSB(a): # MSB is 1 for a negative number
	if a >= 0:  return 0
	else:       return 1

# * Packing is backwards, hardware needs to reverse wire order (from SR to EEPROM)
def reverseByte(byte):
	width = 8 # Number of bits in the byte
	# Flip byte
	byte = '{:0{width}b}'.format(byte, width=width)
	byte = int(byte[::-1], 2)
	return byte

# Functional model that takes in an image and guesses the number (mnist)
def model(image):
	input_layer = image
	num_layers = len(shape) - 1
	for l_index in range(num_layers): # One less: not including the input layer
		prev_size = shape[l_index]
		# Keep track of current layer
		curr_size = shape[l_index + 1]
		curr_layer = []
		curr_packed_nodes = 0
		# Last layer isn't quantized
		last_layer = True if curr_size == shape[-1] else False

		for node in range(curr_size):
			accum = 0
			for w_index in range(prev_size):
				EEPROM_addr = w_index >> 3  # 3 LSBs are for bit selection
				bit_index = w_index & 0b111 # Mask away all but lowest three bits

				# Select bit weight and input data
				# print(bin(weights[l_index][node][EEPROM_addr]))
				weight = weights[l_index][node][EEPROM_addr] & ( 1 << bit_index )
				data = input_layer[EEPROM_addr]              & ( 1 << bit_index )
				# Multiply and add
				mult = XNOR(weight, data)
				accum = UpDown(accum, mult)
			# Save node in some form
			if not last_layer:
				# Quantize (Grab MSB)
				MSB = getMSB(accum)
				val = NOT(MSB)
				# Store value by bit packing again
				curr_packed_nodes |= val
				# If 8 nodes have gone by, packed weights together
				if (node + 1) % 8 == 0: # Don't start with appending
					curr_layer.append(reverseByte(curr_packed_nodes))
					curr_packed_nodes = 0
				else:
					# Shift bits to make room for the next node
					curr_packed_nodes <<= 1

			# Last layer is not quantized
			else: 
				curr_layer.append(accum)

		# Make sure size is appropriate
		if not last_layer:
			EEPROM_size = curr_size >> 3
			# Current layer is going into the previous
			input_layer = curr_layer
		else:
			EEPROM_size = curr_size
		assert EEPROM_size == len(curr_layer), f"Not Enough nodes have been added to current layer - {curr_size} != {len(curr_layer)}"

	# Return actual guess instead of encoded logits vector
	# print(curr_layer)
	answer = curr_layer[0] # Start off guessing it is zero
	index = 0
	for i, challenger in enumerate(curr_layer):
		if challenger >= answer:
			answer = challenger
			index = i

	return index

def test_model(images, answers, bar=True):
	correct = 0
	incorrect = 0
	# Add progress bar unless specified otherwise
	if bar:
		pbar = tqdm(total=len(answers))
	# Iterate through every image given
	for image, answer in zip(images, answers):
		# Flatten image for model
		# Update progress bar
		if bar:
			pbar.update(n=1)
		# Use model to make a prediction
		guess = model(image)
		# print(guess)
		# Evaluate
		if guess == answer:
			correct += 1
		else:
			incorrect += 1
	if bar:
		pbar.close()
	return (correct, incorrect, len(images))

length = 50 # max of 50
print(f"Testing model with {length} image{'s' if length != 1 else ''}")
correct, incorrect, total = test_model(x_test[:length], y_test[:length], bar=True)
print("Accuracy: ", correct/total * 100, "%")