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

# # Test to see that xnor + adder work
weights = [[[0b00000000, 0b11111111, 0b01010101, 0b01100110]]]
inputs =  [[[0b01010101, 0b00000000, 0b01010101, 0b11110000]]]
# Create and fill EEPROMs
WEIGHTS = IC.EEPROM(addr_len=3, name="Weights")
WEIGHTS.fill3D(weights, (0, 0, 3))

INPUTS = IC.EEPROM(addr_len=3, name="Input")
INPUTS.fill3D(inputs, (0, 0, 3))

# Create select lines for MUXs
prgm_counter = asyncIC.pins(6, name="PC")
sel = prgm_counter[0:3]
addr = prgm_counter[3:6]

# Create and wire MUXs
W_MUX = asyncIC.Multiplexor(out_len=1, name="Weights Mux")
I_MUX = asyncIC.Multiplexor(out_len=1, name="Inputs Mux") 
W_MUX.wire(WEIGHTS.io_pins, sel)
I_MUX.wire(INPUTS.io_pins, sel)

# Wire addresses to EEPROMs
WEIGHTS.wire(addr)
INPUTS.wire(addr)

# Create MULTIPLIER
xnor = asyncIC.Multiplier(name="XNOR")
xnor.wire(W_MUX.output, I_MUX.output)

# Create ADDER
accum = IC.UpDownCounter(name="accum")
accum.wire(xnor.output)

print('Weight\tInput\tAccum')
for i in range(1 << 6):
    prgm_counter.value = i
    accum.update()
    print(f"{W_MUX.raw}\t{I_MUX.raw}\t{accum.raw}")
