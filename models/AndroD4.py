# AUTHOR: Daniel Raymond
# DATE  : 2020-04-012
# ABOUT : Neural network using packed bits technique and bitwise operators

import os
import sys
sys.path.append('c:\\Users\\dan\\Desktop\\Projects\\Andro\\src')

# Supress Tensorflow dll warning
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from weights import weights, biases, mnist
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
# from tqdm import tqdm


