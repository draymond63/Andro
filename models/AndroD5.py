# AUTHOR: Daniel Raymond
# DATE  : 2020-04-013
# ABOUT : Using chip definitions to create model

from src.data_packed import x_test, y_test, weights, shape
import sim.ChipsD0 as IC
import sim.ChipsGen as asyncIC
import sim.ChipsLogical as logIC
from tqdm import tqdm

BITS_LAYER = 1
BITS_NODES = 9
BITS_WEIGHTS = 7

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
        self.WEIGHTS_EEPROM.fill3D(weights, (BITS_LAYER, BITS_NODES, BITS_WEIGHTS))
        self.INPUT1_EEPROM = IC.EEPROM(addr_len=7, name='INPUT1')
        # ? self.INPUT2_EEPROM = IC.EEPROM(addr_len=7, name='INPUT2') # ? Storage EEPROM
        # MINIMUM address bits for current model - 2 (784, 512, 10)
        # ? self.SHAPE_EEPROM = IC.EEPROM(addr_len=2, name="SHAPE")
        # ? self.SHAPE_EEPROM.fill3D(shape, (0, 0, 2))
        self.INPUT_SIZE =        IC.FlipFlop(10, val=784, name="CONST_IN_SIZE")
        self.HIDDEN_LAYER_SIZE = IC.FlipFlop(10, val=512, name="CONST_HL_SIZE")
        self.OUTPUT_SIZE =       IC.FlipFlop(10, val=10, name="CONST_OUT_SIZE")

    def _initMult(self):
        # MUXs
        self.W_MUX = asyncIC.Multiplexor(out_len=1, name='Weights Mux')
        self.I_MUX = asyncIC.Multiplexor(out_len=1, name='Inputs Mux')
        # MULTIPLIER
        self.XNOR = asyncIC.XNOR(name='XNOR')
        self.XNOR.wire(self.W_MUX.output, self.I_MUX.output)
        # ADDER
        self.accum = IC.UpDownCounter(name='Accum')
        self.accum.wire(self.XNOR.output)

    def _initCounters(self):
        # Sizes match those of EEPROMS
        self.layer_counter = IC.Counter(BITS_LAYER, name="L_COUNT")
        self.node_counter = IC.Counter(BITS_NODES, name="N_COUNT")
        self.weight_counter = IC.Counter(BITS_WEIGHTS, name="W_COUNT")

        # Comparison outputs to notify when to increment
        self.layer_comp = asyncIC.XNOR(BITS_NODES, name="L_DONE")
        self.node_comp = asyncIC.XNOR(BITS_WEIGHTS, name="N_DONE")
    
    # Given an image, returns the value
    def predict(self, x):
        self.INPUT1_EEPROM.fill3D([[x]], (0, 0, 7))
        

    def grabAndMult(self):
        pass

# ### Test to see that xnor + adder work
# weights = [[[0b00000000, 0b11111111, 0b01010101, 0b01100110]]]
# inputs =  [[[0b01010101, 0b00000000, 0b01010101, 0b11110000]]]
# # Create and fill EEPROMs
# WEIGHTS = IC.EEPROM(addr_len=3, name='Weights')
# WEIGHTS.fill3D(weights, (0, 0, 2))

# INPUTS = IC.EEPROM(addr_len=3, name='Input')
# INPUTS.fill3D(inputs, (0, 0, 2))

# # Create select lines for MUXs
# PC = IC.Counter(6, name="PC")
# sel = PC.output[0:3]
# addr = PC.output[3:6]

# # Create and wire MUXs
# W_MUX = asyncIC.Multiplexor(out_len=1, name='Weights Mux')
# I_MUX = asyncIC.Multiplexor(out_len=1, name='Inputs Mux') 
# W_MUX.wire(WEIGHTS.output, sel)
# I_MUX.wire(INPUTS.output, sel)

# # Wire addresses to EEPROMs
# WEIGHTS.wire(addr)
# INPUTS.wire(addr)

# # MUXs
# W_MUX = asyncIC.Multiplexor(out_len=1, name='Weights Mux')
# I_MUX = asyncIC.Multiplexor(out_len=1, name='Inputs Mux')
# W_MUX.wire(WEIGHTS.output, sel)
# I_MUX.wire(INPUTS.output, sel)
# # MULTIPLIER
# XNOR = asyncIC.XNOR(1, name='Multiplier')
# XNOR.wire(W_MUX.output, I_MUX.output)
# # ADDER
# accum = IC.UpDownCounter(name='Accum')
# accum.wire(XNOR.output)

# # Create a clock to tether
# clk = asyncIC.CLOCK([accum, PC]) # PC, accum is wrong

# for i in range(len(weights[0][0]) * 8):
#     clk.pulse()
#     print(f'{W_MUX}\t\t{I_MUX}\t\t{accum}')
# print(accum)

a = asyncIC.pins(10)
b = asyncIC.pins(10)
comp = logIC.COMPARE(10, name="COMPARE")
comp.wire(a, b)

for i in range(10):
    a.value = i % 5
    b.value = i % 7
    print(a.raw, b.raw, comp)
