# AUTHOR: Daniel Raymond
# DATE  : 2020-04-013
# ABOUT : Using chip definitions to create model

from src.data_packed import x_test, y_test, weights, shape
import sim.ChipsD0 as IC
import sim.ChipsGen as asyncIC
from tqdm import tqdm

class model():
    def __init__(self):
        # Weights currently require 98 kB : addr_len >= 17
        self.WEIGHTS_EEPROM = IC.EEPROM(addr_len=18, name="Weights")
        self.WEIGHTS_EEPROM.fill3D(weights, (3, 7, 8)) # ! Random Shape
        self.INPUT1_EEPROM = IC.EEPROM(addr_len=10, name="INPUT1")
    
    # Given an image, returns the value
    def predict(self, x):
        self.INPUT1_EEPROM.fill3D([x], (0, 5, 5))
        pass
