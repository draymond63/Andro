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

class Model():
    def __init__(self):
        self._initEEPROM()
        self._initMult()
        self._initCounters()
        self._wireEEPROM()

        self.clk = asyncIC.CLOCK([
            self.accum,
            self.weight_counter,
        ])

    def _initEEPROM(self):
        # Weights currently require 98 kB : addr_len >= 17 if packed to the max
        self.WEIGHTS_EEPROM = IC.EEPROM(addr_len=17, name='WEIGHTS')
        # * Current model max dimensions - # of: layers=2, nodes=512, weights-bytes-in-node=98
        # MINIMUM address bits for current model - 1, 9, 7
        self.WEIGHTS_EEPROM.fill3D(weights, (BITS_LAYER, BITS_NODES, BITS_WEIGHTS))
        self.INPUT1_EEPROM = IC.EEPROM(addr_len=16, name='INPUT1')
        # ? self.INPUT2_EEPROM = IC.EEPROM(addr_len=7, name='INPUT2') # ? Storage EEPROM
        # MINIMUM address bits for current model - 2 (784, 512, 10)
        # ? self.SHAPE_EEPROM = IC.EEPROM(addr_len=2, name="SHAPE")
        # ? self.SHAPE_EEPROM.fill3D(shape, (0, 0, 2))
        self.INPUT_SIZE = IC.FlipFlop(10, val=784, name="SHAPE_WEIGHT_COUNT")
        self.LAYER_SIZE = IC.FlipFlop(10, val=512, name="SHAPE_NODE_COUNT")
        self.LAYER_SIZE.wire(self.INPUT_SIZE.output) # ? Add a clock

    def _initMult(self):
        # MUXs
        self.W_MUX = asyncIC.Multiplexor(out_len=1, name='Weights Mux')
        self.I_MUX = asyncIC.Multiplexor(out_len=1, name='Inputs Mux')
        # MULTIPLIER
        self.XNOR = asyncIC.XNOR(name='XNOR')
        self.XNOR.wire(self.W_MUX.output, self.I_MUX.output)
        # ADDER
        self.accum = IC.UpDownCounter(10, name='Accum')
        self.accum.wire(self.XNOR.output)

    def _initCounters(self):
        # Sizes match those of EEPROMS
        self.layer_counter = IC.Counter(BITS_LAYER, name="L_COUNT")
        self.node_counter = IC.Counter(10, name="N_COUNT")
        self.weight_counter = IC.Counter(10, name="W_COUNT")
        # * Comparison outputs to notify when to increment
        self.node_done = logIC.COMPARE(10, name="L_DONE")
        self.weight_done = logIC.COMPARE(10, name="N_DONE")
        # Wire to inputs
        self.node_done.wire(self.node_counter.output, self.LAYER_SIZE.output)
        self.weight_done.wire(self.weight_counter.output, self.INPUT_SIZE.output)
        # Wire to each other
        self.node_counter.wire(self.weight_done.output)
        self.layer_counter.wire(self.node_done.output)
        
    def _wireEEPROM(self):
        sel = self.weight_counter.output[0:3]       # 3 pins (MUX)
        addr1 = self.weight_counter.output[3:10]    # 7 pins
        addr2 = self.node_counter.output[0:9]       # 9 pins
        addr3 = self.layer_counter.output           # 1 pin
        w_addr = asyncIC.pins(pins_list=(addr1, addr2, addr3))
        i_addr = asyncIC.pins(pins_list=(addr1, addr2))
        # MUXs
        self.W_MUX.wire(self.WEIGHTS_EEPROM.output, sel)
        self.I_MUX.wire(self.INPUT1_EEPROM.output, sel)
        # EEPROMs
        self.WEIGHTS_EEPROM.wire(w_addr)
        self.INPUT1_EEPROM.wire(i_addr)

    
    # Given an image, returns the value
    def predict(self, x):
        self.INPUT1_EEPROM.fill3D([[x]], (0, 0, 7))
        self.nodeMult()
        return self.accum.raw
        
    def nodeMult(self):
        while not self.weight_done:
            self.clk.pulse()


model = Model()
model.predict(x_test[0])

# x = [1, 2, 3]
# print(x)
# print(list(x))

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

