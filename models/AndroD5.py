# AUTHOR: Daniel Raymond
# DATE  : 2020-04-013
# ABOUT : Using chip definitions to create model

from src.data_packed import x_test, y_test, weights, shape
import sim.ChipsClocked as IC
import sim.ChipsAsync as asyncIC
import sim.ChipsLogical as logIC
# from tqdm import tqdm

BITS_LAYER = 1
BITS_NODES = 9
BITS_WEIGHTS = 7

class Model():
    def __init__(self):
        self.clk = IC.CLOCK()

        self._initEEPROM()
        self._initCounters()
        self._initRDSignals()
        self._initMult()
        self._initSrRestore()
        self._initAddrRestore()
        self._wireEEPROM()

        self.clk.sync(self.accum)
        self.clk.sync(self.weight_counter)

    def _initEEPROM(self):
        # Weights currently require 98 kB : addr_len >= 17 if packed to the max
        self.WEIGHTS_EEPROM = asyncIC.EEPROM(addr_len=17, name='WEIGHTS')
        # * Current model max dimensions - # of: layers=2, nodes=512, weights-bytes-in-node=98
        # MINIMUM address bits for current model - 1, 9, 7
        self.WEIGHTS_EEPROM.fill3D(weights, (BITS_LAYER, BITS_NODES, BITS_WEIGHTS))
        self.INPUT1_EEPROM = asyncIC.EEPROM(addr_len=16, name='INPUT1')
        self.INPUT2_EEPROM = asyncIC.EEPROM(addr_len=16, name='INPUT2') # ? Storage EEPROM
        # MINIMUM address bits for current model - 2 (784, 512, 10)
        # ? self.SHAPE_EEPROM = asyncIC.EEPROM(addr_len=2, name='SHAPE')
        # ? self.SHAPE_EEPROM.fill3D(shape, (0, 0, 2))
        self.INPUT_SIZE = IC.FlipFlop(10, val=784, name='SHAPE_WEIGHT_COUNT')
        self.LAYER_SIZE = IC.FlipFlop(10, val=512, name='SHAPE_NODE_COUNT')
        self.LAYER_SIZE.wire(self.INPUT_SIZE.output) # ? Add a clock

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
        self.layer_counter.wire(self.nodes_done.output)

    def _initRDSignals(self):
        # LSB of layer counter choose between EEPROMs
        self.I1_RD = self.layer_counter.output[0:1] # 0: READ INPUT2, 1: READ INPUT1
        # Other RD single
        I2_RD = asyncIC.NOT(1, name='I1/2-SEL')
        I2_RD.wire(self.I1_RD)
        self.I2_RD = I2_RD.output
        # RD_WR needs to be delayed one clk cycle (HW - Combine these into one flipflop)
        self.I1_RD_delayed = IC.FlipFlop(1, name='I1-Read (#1)')
        self.I1_RD_delayed.wire(self.I1_RD, self.clk)
        self.I2_RD_delayed = IC.FlipFlop(1, name='I2-Read (#1)')
        self.I2_RD_delayed.wire(self.I2_RD, self.clk)
        # Reference the output pins
        self.I1_RD_delayed = self.I1_RD_delayed.output
        self.I2_RD_delayed = self.I2_RD_delayed.output

    def _initMult(self):
        # MUXs
        self.W_OUT_MUX = asyncIC.bitMux(name='Weights-Mux')
        self.I1_OUT_MUX = asyncIC.bitMux(name='I1-Out-Mux')
        self.I2_OUT_MUX = asyncIC.bitMux(name='I2-Out-Mux') 
        # Select between the output of the two EEPROMS
        self.I_TOT_MUX = asyncIC.Mux(1, name='Final-Input-Mux')
        self.I_TOT_MUX.wire(self.I2_OUT_MUX.output, self.I1_OUT_MUX.output, self.I1_RD)
        # MULTIPLIER
        self.XNOR = asyncIC.XNOR(name='Multiplier')
        self.XNOR.wire(self.W_OUT_MUX.output, self.I_TOT_MUX.output)
        # ADDER
        self.accum = IC.UpDownCounter(10, name='Accum')
        self.accum.wire(self.XNOR.output)

    def _initSrRestore(self):
        self.I1_SR = IC.ShiftRegister(name='I1-SR')
        self.I2_SR = IC.ShiftRegister(name='I2-SR')
        # AND write and clk to know when to shift in
        I1_SR_CLK = asyncIC.AND(1)
        I2_SR_CLK = asyncIC.AND(1)
        I1_SR_CLK.wire(self.weights_done.output, self.I1_RD) # Active when its EEPROM is reading
        I2_SR_CLK.wire(self.weights_done.output, self.I2_RD)
        # Wire input of SRs to LSB of accum
        i = self.accum.width
        MSB = self.accum.output[i-1:i] # Take the MSB
        quantI = asyncIC.NOT(name='Accum-Quantized')
        quantI.wire(MSB)
        # Wire input of SRs
        self.I1_SR.wire(quantI.output, I1_SR_CLK.output)
        self.I2_SR.wire(quantI.output, I2_SR_CLK.output)
        # Flash pins
        self.I1_Flash = asyncIC.pins(1, name="I1-Flash")
        self.I2_Flash = asyncIC.pins(1, name="I2-Flash")
        # Reverse output of SR because data is loaded in backwards
        self.I1_SR_OUT = self.I1_SR.output[::-1]
        self.I2_SR_OUT = self.I2_SR.output[::-1]

    def _initAddrRestore(self):
        # Rearrange outputing address lines
        addr1 = self.weight_counter[3:10]    # 7 pins
        addr2 = self.node_counter[0:9]       # 9 pins
        self.w_addr = asyncIC.pins(pins_list=(addr1, addr2, self.layer_counter.output)) # 17 pins
        # Input EEPROMs address deciding
        self.i_addr_active = asyncIC.pins(pins_list=(addr1, addr2), name='I-ADDR-AC') # 16 pins
        self.i_addr_listen = IC.FlipFlop(6, name='I-ADDR-LS') # 6 pins (Flipflop inbetween mux and addr2[3:9] to delay the signal)
        self.i_addr_listen.wire(self.node_counter[3:9], clk=self.clk) # Updates every clock cycle
        # MUXs to select between the two possible address lines
        self.I1_ADDR_MUX = asyncIC.Mux(16, name='I1-ADDR-MUX')
        self.I2_ADDR_MUX = asyncIC.Mux(16, name='I2-ADDR-MUX')
        # ? Shouldn't i_addr_listen be 7 pins to match the number of weight pins used?
        self.I1_ADDR_MUX.wire(self.i_addr_active, self.i_addr_listen.output, self.I1_RD_delayed)
        self.I2_ADDR_MUX.wire(self.i_addr_active, self.i_addr_listen.output, self.I2_RD_delayed)

    def _wireEEPROM(self):        
        # MUXs
        sel = self.weight_counter.output[0:3]  # 3 pins (MUX)
        self.W_OUT_MUX.wire(self.WEIGHTS_EEPROM.output, sel)
        self.I1_OUT_MUX.wire(self.INPUT1_EEPROM.output, sel)
        ### EEPROMs
        self.WEIGHTS_EEPROM.wire(self.w_addr)
        # Address switches 'i_addr' to 'self.node_counter // 8' depending on the r/w state
        self.INPUT1_EEPROM.wire(addr=self.I1_ADDR_MUX.output, data_in=self.I1_SR_OUT, rd_wr=self.I1_RD_delayed, flash=self.I1_Flash)
        self.INPUT2_EEPROM.wire(addr=self.I2_ADDR_MUX.output, data_in=self.I2_SR_OUT, rd_wr=self.I2_RD_delayed, flash=self.I2_Flash)

    # * CALCULATION FUNCTIONS (Should be removed in final iteration except predict function)
    # Given an image, returns the value
    def predict(self, x, start=(0, 0, 0)):
        self.INPUT1_EEPROM.fill3D([[x]], (0, 0, 7))

        self.layer_counter.value = start[0] # Start at a later part in the sim if requested
        self.node_counter.value = start[1]
        self.weight_counter.value = start[2] 

        self.layerMult()

    def layerMult(self):
        while not self.nodes_done:
            self.nodeMult()
            if self.node_counter.raw % 8 == 0:
                print("FLASHING:", self.i_addr_listen.data_in, self.i_addr_listen.output, self.INPUT2_EEPROM.addr)
                self.I2_Flash.value = 1
                self.I2_Flash.value = 0
        
        print(self.INPUT2_EEPROM.rd_wr)
        print(self.INPUT2_EEPROM.data[0])
        print(self.node_counter.raw, ': ', self.INPUT2_EEPROM.data[62:64], '\t', self.I2_SR_OUT, flush=True)

        self.clk.pulse() # One mroe clock pulse and the rd/wr changes


        
    def nodeMult(self):
        while not self.weights_done:
            self.clk.pulse()
        self.accum.value = 0
        self.weight_counter.value = 0

model = Model()
model.predict(x_test[0], (0, 480, 0))


