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
        self.clk = asyncIC.CLOCK()

        self._initEEPROM()
        self._initMult()
        self._initCounters()
        self._initRestore()
        self._wireEEPROM()

        self.clk.sync(self.accum)
        self.clk.sync(self.weight_counter)

    def _initEEPROM(self):
        # Weights currently require 98 kB : addr_len >= 17 if packed to the max
        self.WEIGHTS_EEPROM = IC.EEPROM(addr_len=17, name='WEIGHTS')
        # * Current model max dimensions - # of: layers=2, nodes=512, weights-bytes-in-node=98
        # MINIMUM address bits for current model - 1, 9, 7
        self.WEIGHTS_EEPROM.fill3D(weights, (BITS_LAYER, BITS_NODES, BITS_WEIGHTS))
        self.INPUT1_EEPROM = IC.EEPROM(addr_len=16, name='INPUT1')
        self.INPUT2_EEPROM = IC.EEPROM(addr_len=16, name='INPUT2') # ? Storage EEPROM
        # MINIMUM address bits for current model - 2 (784, 512, 10)
        # ? self.SHAPE_EEPROM = IC.EEPROM(addr_len=2, name='SHAPE')
        # ? self.SHAPE_EEPROM.fill3D(shape, (0, 0, 2))
        self.INPUT_SIZE = IC.FlipFlop(10, val=784, name='SHAPE_WEIGHT_COUNT')
        self.LAYER_SIZE = IC.FlipFlop(10, val=512, name='SHAPE_NODE_COUNT')
        self.LAYER_SIZE.wire(self.INPUT_SIZE.output) # ? Add a clock

    def _initMult(self):
        # MUXs
        self.W_MUX = asyncIC.Multiplexor(out_len=1, name='Weights-Mux')
        self.I_MUX = asyncIC.Multiplexor(out_len=1, name='Inputs-Mux')
        # MULTIPLIER
        self.XNOR = asyncIC.XNOR(name='Multiplier')
        self.XNOR.wire(self.W_MUX.output, self.I_MUX.output)
        # ADDER
        self.accum = IC.UpDownCounter(10, name='Accum')
        self.accum.wire(self.XNOR.output)

    def _initCounters(self):
        # Sizes should match those of EEPROMS
        self.layer_counter = IC.Counter(BITS_LAYER, name='L-COUNT')
        self.node_counter = IC.Counter(10, name='N-COUNT')
        self.weight_counter = IC.Counter(10, name='W-COUNT')
        # * Comparison outputs to notify when to increment
        self.nodes_done = logIC.COMPARE(10, name='L-DONE')
        self.weights_done = logIC.COMPARE(10, name='N-DONE')
        # Wire to inputs
        self.nodes_done.wire(self.node_counter.output, self.LAYER_SIZE.output)
        self.weights_done.wire(self.weight_counter.output, self.INPUT_SIZE.output)
        # Wire to each other
        self.node_counter.wire(self.weights_done.output)
        self.layer_counter.wire(self.nodes_done.output) #! Shit breaks

    def _initRestore(self):
        self.I1_SR = IC.ShiftRegister(name='I1-SR')
        self.I2_SR = IC.ShiftRegister(name='I2-SR')
        # LSB of layer counter choose between EEPROMs
        self.EEPROM2_RD = self.layer_counter.output[0:1] # 0: INPUT2, 1: INPUT1
        self.EEPROM1_RD = asyncIC.NOT(1).output
        self.EEPROM1_RD.wire(self.EEPROM2_RD)
        # AND write and clk to know when to shift in
        I1_SR_CLK = asyncIC.AND(1)
        I2_SR_CLK = asyncIC.AND(1)
        I1_SR_CLK.wire(self.clk.output, self.EEPROM2_RD)
        I2_SR_CLK.wire(self.clk.output, self.EEPROM1_RD)
        # Wire input of SRs to LSB of accum
        i = self.accum.width
        MSB = self.accum.output[i-1:i] # Take the MSB
        # Wire input of SRs
        self.I1_SR.wire(MSB, I1_SR_CLK.output)
        self.I2_SR.wire(MSB, I2_SR_CLK.output)
        
    def _wireEEPROM(self):
        # Rearrange Address Lines
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
        self.INPUT1_EEPROM.wire(i_addr, self.I1_SR.output, self.EEPROM1_RD, asyncIC.pins(1))
        self.INPUT2_EEPROM.wire(i_addr, self.I2_SR.output, self.EEPROM2_RD, asyncIC.pins(1))

    # * CALCULATION FUNCTIONS (Should be removed in final iteration)
    # Given an image, returns the value
    def predict(self, x):
        self.INPUT1_EEPROM.fill3D([[x]], (0, 0, 7))
        self.layerMult()

    def layerMult(self):
        while not self.nodes_done:
            print(self.node_counter.raw, end=": ")
            self.nodeMult()
        
    def nodeMult(self):
        while not self.weights_done:
            self.clk.pulse()
        print(self.accum.raw)
        self.resetNode()
        self.clk.pulse()

    def resetNode(self):
        self.accum.value = 0
        self.weight_counter.value = 0
    
    def storeBit(self):
        bit = self.accum.value[-1]
        # self.I1_SR

model = Model()
model.predict(x_test[0])