# AUTHOR: Daniel Raymond
# DATE  : 2020-04-013
# ABOUT : Using chip definitions to create model

from src.data_packed import x_test, y_test, weights, shape
import sim.ChipsD0 as IC
import sim.ChipsGen as asyncIC
from tqdm import tqdm

class model():
    def __init__(self):
        self._initEEPROM()
        self._initMult()
        self._initCounters()

    def _initEEPROM(self):
        # Weights currently require 98 kB : addr_len >= 17 if packed to the max
        self.WEIGHTS_EEPROM = IC.EEPROM(addr_len=18, name='WEIGHTS')
        # * Current model max dimensions - # of: layers=2, nodes=512, weights-bytes-in-node=98
        # MINIMUM address bits for current model - 1, 9, 7
        self.WEIGHTS_EEPROM.fill3D(weights, (1, 9, 7))
        self.INPUT1_EEPROM = IC.EEPROM(addr_len=10, name='INPUT1')
        # ? self.INPUT2_EEPROM = IC.EEPROM(addr_len=10, name='INPUT2') # ? Storage EEPROM
        # MINIMUM address bits for current model - 2 (784, 512, 10)
        self.SHAPE_EEPROM = IC.EEPROM(addr_len=2, name="SHAPE")
        self.SHAPE_EEPROM.fill3D(shape, (0, 0, 2))

    def _initMult(self):
        # MUXs
        self.W_MUX = asyncIC.Multiplexor(out_len=1, name='Weights Mux')
        self.I_MUX = asyncIC.Multiplexor(out_len=1, name='Inputs Mux')
        # MULTIPLIER
        self.XNOR = asyncIC.Multiplier(name='XNOR')
        self.XNOR.wire(W_MUX.output, I_MUX.output)
        # ADDER
        self.accum = IC.UpDownCounter(name='Accum')
        self.accum.wire(self.XNOR.output)

    def _initCounters(self):
        self.LayerCounter = IC.Counter(2, name="L_COUNT")
    
    # Given an image, returns the value
    def predict(self, x):
        self.INPUT1_EEPROM.fill3D([[x]], (0, 0, 10))
        

    def grabAndMult(self):
        pass

# # Test to see that xnor + adder work
weights = [[[0b00000000, 0b11111111, 0b01010101, 0b01100110]]]
inputs =  [[[0b01010101, 0b00000000, 0b01010101, 0b11110000]]]
# Create and fill EEPROMs
WEIGHTS = IC.EEPROM(addr_len=3, name='Weights')
WEIGHTS.fill3D(weights, (0, 0, 3))

INPUTS = IC.EEPROM(addr_len=3, name='Input')
INPUTS.fill3D(inputs, (0, 0, 3))

# Create select lines for MUXs
PC = IC.Counter(6, name="PC")
sel = PC.output[0:3]
addr = PC.output[3:6]

# Create and wire MUXs
W_MUX = asyncIC.Multiplexor(out_len=1, name='Weights Mux')
I_MUX = asyncIC.Multiplexor(out_len=1, name='Inputs Mux') 
W_MUX.wire(WEIGHTS.output, sel)
I_MUX.wire(INPUTS.output, sel)

# Wire addresses to EEPROMs
WEIGHTS.wire(addr)
INPUTS.wire(addr)

# MUXs
W_MUX = asyncIC.Multiplexor(out_len=1, name='Weights Mux')
I_MUX = asyncIC.Multiplexor(out_len=1, name='Inputs Mux')
W_MUX.wire(WEIGHTS.output, sel)
I_MUX.wire(INPUTS.output, sel)
# MULTIPLIER
XNOR = asyncIC.Multiplier(name='XNOR')
XNOR.wire(W_MUX.output, I_MUX.output)
# ADDER
accum = IC.UpDownCounter(name='Accum')
accum.wire(XNOR.output)

# Increment PC
clk = asyncIC.pins(1, name="CLK")
PC.wire(clk)
for i in range(4 * 8):
    accum.update()
    print(f'{W_MUX}\t\t{I_MUX}\t\t{accum}')
    clk.raw ^= 1 # Toggle clock
