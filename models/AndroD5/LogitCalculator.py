# AUTHOR: Daniel Raymond
# DATE  : 2020-04-013
# ABOUT : Main body -> Takes input image and calculates logits

from src.model_packed import weights, shape
from src.data_packed import x_test, y_test
import ChipsClocked as IC
import ChipsAsync as asyncIC
from tqdm import tqdm

BITS_LAYER = 2
BITS_NODES = 9
BITS_WEIGHTS = 7

class Model():
    def __init__(self):
        self.bar = True # Display variable
        self.clk = IC.CLOCK()

        self._initEEPROMs()
        self._initCounters()
        self._initRDSignals()
        self._initMult()
        self._initSrRestore()
        self._initAddrRestore()
        self._wireEEPROM()

        self.clk.sync([
            self.accum,
            self.weight_counter,
        ])
        # I1_RD_delayed, I2_RD_delayed, i_addr_listen, layer_done_delayed

    def _initEEPROMs(self):
        # Weights currently require 98 kB : addr_len >= 17 if packed to the max
        self.WEIGHTS_EEPROM = asyncIC.EEPROM(addr_len=18, name='WEIGHTS')
        # * Current model max dimensions - # of: layers=2, nodes=512, weights-bytes-in-node=98
        # MINIMUM address bits for current model - 1, 9, 7
        self.WEIGHTS_EEPROM.fill3D(weights, (BITS_LAYER, BITS_NODES, BITS_WEIGHTS))
        # Alternating data EEPROMs
        self.INPUT1_EEPROM = asyncIC.EEPROM(addr_len=7, name='INPUT1')
        self.INPUT2_EEPROM = asyncIC.EEPROM(addr_len=7, name='INPUT2') # ? Storage EEPROM
        # MINIMUM address bits for current model - 2 (784, 512, 10)
        self.SHAPE_EEPROM = asyncIC.EEPROM(addr_len=2, io_len=10, name='SHAPE')
        self.SHAPE_EEPROM.fill(shape)
        self.INPUT_SIZE = IC.FlipFlop(10, val=784, name='SHAPE_WEIGHT_COUNT')
        self.LAYER_SIZE = IC.FlipFlop(10, val=512, name='SHAPE_NODE_COUNT')

    def _initCounters(self):
        # Sizes should match those of EEPROMS
        self.layer_counter = IC.Counter(BITS_LAYER, name='L-COUNT')
        self.node_counter = IC.Counter(10, name='N-COUNT')
        self.weight_counter = IC.Counter(10, name='W-COUNT')
        # * Comparison outputs to notify when to increment
        self.model_done = asyncIC.IdentityComparator(10, name='M-DONE')
        self.layer_done = asyncIC.IdentityComparator(10, name='L-DONE')
        self.node_done = asyncIC.IdentityComparator(10, name='N-DONE')
        # Wire to inputs
        zero = asyncIC.pins(10, name='GND')
        self.model_done.wire(self.LAYER_SIZE.output, zero) # HW - default in shape EEPROM is 0xFF, not ground
        self.layer_done.wire(self.node_counter.output, self.LAYER_SIZE.output)
        self.node_done.wire(self.weight_counter.output, self.INPUT_SIZE.output)
        # Wire to each other
        self.node_counter.wire(clk=self.node_done.output)
        self.layer_counter.wire(clk=self.layer_done.output)
        # Create delayed signal for shifting the shape
        self.layer_done_delayed = IC.FlipFlop(1, name='L-DONE #1')
        self.layer_done_delayed.wire(self.layer_done.output, self.clk)
        self.layer_done_delayed = self.layer_done_delayed.output
        # Wire SHAPE output
        self.INPUT_SIZE.wire(self.LAYER_SIZE.output,  self.layer_done_delayed) # ? clk order matters?
        self.LAYER_SIZE.wire(self.SHAPE_EEPROM.output, self.layer_done_delayed) # ! Wire to init clock OR'd with layer_done

    def _initRDSignals(self):
        # LSB of layer counter choose between EEPROMs
        self.I2_RD = self.layer_counter[0:1] # 0: READ INPUT1, 1: READ INPUT2 (read from 1 first - it has the image)
        self.I2_RD.name = 'I2-Read'
        # Other RD single is the opposite of I1-RD
        I1_RD = asyncIC.NOT(1, name='I1-Read')
        I1_RD.wire(self.I2_RD)
        self.I1_RD = I1_RD.output
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
        # SRs
        self.I1_SR = IC.ShiftRegister(name='I1-SR')
        self.I2_SR = IC.ShiftRegister(name='I2-SR')
        # AND write and clk to know when to shift in
        I1_SR_CLK = asyncIC.AND(1)
        I2_SR_CLK = asyncIC.AND(1)
        I1_SR_CLK.wire(self.node_done.output, self.I2_RD) # Active when its EEPROM is being written to (OTHER EEPROM IS BEING READ FROM)
        I2_SR_CLK.wire(self.node_done.output, self.I1_RD)
        # Wire input of SRs to LSB of accum
        i = self.accum.width
        MSB = self.accum.output[i-1:i] # Take the MSB
        quantI = asyncIC.NOT(name='Accum-Quantized')
        quantI.wire(MSB)
        # Wire input of SRs
        self.I1_SR.wire(quantI.output, I1_SR_CLK.output)
        self.I2_SR.wire(quantI.output, I2_SR_CLK.output)
        # Flash pins (activates when node_counter % 8 == 0 (3 LSB == 0))
        self.input_flash = asyncIC.bitNOR(3, name='INPUT-FLASH')
        self.input_flash.wire(self.node_counter[0:3])
        self.input_flash_delayed = IC.FlipFlop(1, name='INPUT-FLASH #1')
        self.input_flash_delayed.wire(self.input_flash.output, self.node_done.output)
        # Reverse output of SR because data is loaded in backwards
        self.I1_SR_OUT = self.I1_SR.output[::-1]
        self.I2_SR_OUT = self.I2_SR.output[::-1]

    def _initAddrRestore(self):
        # Rearrange outputting address lines
        weight_incr = self.weight_counter[3:10]    # 7 pins
        self.w_addr = asyncIC.pins(pins_list=(weight_incr, self.node_counter[0:9], self.layer_counter.output)) # 17 pins
        # Input EEPROMs address deciding
        self.i_addr_active = weight_incr
        self.i_addr_active.name = 'I-ADDR-AC'
        self.i_addr_listen = IC.FlipFlop(7, name='I-ADDR-LS') # 7 pins (Flipflop inbetween mux and node_counter // 8 to delay the signal)
        self.i_addr_listen.wire(self.node_counter[3:10], clk=self.clk) # Updates every clock cycle
        # MUXs to select between the two possible address lines
        self.I1_ADDR_MUX = asyncIC.Mux(7, name='I1-ADDR-MUX')
        self.I2_ADDR_MUX = asyncIC.Mux(7, name='I2-ADDR-MUX')
        # MUX selection wiring
        self.I1_ADDR_MUX.wire(self.i_addr_listen.output, self.i_addr_active, self.I1_RD_delayed)
        self.I2_ADDR_MUX.wire(self.i_addr_listen.output, self.i_addr_active, self.I2_RD_delayed)

    def _wireEEPROM(self):        
        # MUXs
        sel = self.weight_counter.output[0:3]  # 3 pins (MUX)
        self.W_OUT_MUX.wire(self.WEIGHTS_EEPROM.output, sel)
        self.I1_OUT_MUX.wire(self.INPUT1_EEPROM.output, sel)
        self.I2_OUT_MUX.wire(self.INPUT2_EEPROM.output, sel)
        ### EEPROMs
        self.WEIGHTS_EEPROM.wire(self.w_addr)
        # Address switches 'i_addr' to 'self.node_counter // 8' depending on the r/w state  # * FLIP RD_WR SIGNAL SINCE RD IS ACTIVE LOW
        self.INPUT1_EEPROM.wire(addr=self.I1_ADDR_MUX.output, data_in=self.I1_SR_OUT, rd_wr=self.I2_RD_delayed, flash=self.input_flash_delayed.output)
        self.INPUT2_EEPROM.wire(addr=self.I2_ADDR_MUX.output, data_in=self.I2_SR_OUT, rd_wr=self.I1_RD_delayed, flash=self.input_flash_delayed.output)

    # * CALCULATION FUNCTIONS (Should be removed in final iteration except predict function)
    # Given an image, returns the value
    def predict(self, x, start=(0, 0, 0)):
        self.INPUT1_EEPROM.fill(x)
        self.SHAPE_EEPROM

        self.layer_counter.value = start[0] # Start at a later part in the sim if requested
        self.node_counter.value = start[1]
        self.weight_counter.value = start[2] 

        self.modelMult()
        # self.layerMult()
        # self.nodeMult()
        print(self.INPUT1_EEPROM.data[0:10])

    def modelMult(self):
        while not self.model_done:
            self.layerMult()
            self.bar = False
            
    def layerMult(self):
        if self.bar:
            pbar = tqdm(total=self.LAYER_SIZE.raw  - self.node_counter.raw)

        while not self.layer_done:
            self.nodeMult()
            if self.bar:
                pbar.update(n=1)
        
        if self.layer_counter.raw == 1: # On the first iteration, load 10 temporarily
            self.SHAPE_EEPROM.output.value = 10
        self.clk.pulse() # One more clock pulse and the rd/wr changes
        self.accum.value = 0 # Reset (This is needed because of the extra clock pulse?)
        self.weight_counter.value = 0

        self.node_counter.value = 0
        self.SHAPE_EEPROM.output.value = 0 # Notify this the last layer

        self.INPUT2_EEPROM.data[63] >>= 1 # ! Correct value because it's wrong

        if self.bar:
            pbar.close()

    def nodeMult(self):
        while not self.node_done:
            self.clk.pulse()
        
        # ! Layer goes to 2 for some dumbass reason (delay layer_counter incrementing)
        if self.layer_counter.raw >= 1 and self.node_counter != 511: 
            print(self.node_counter.raw - 1, self.accum.raw) # node increments then we print, so - 1

        self.accum.value = 0
        self.weight_counter.value = 0

model = Model()
model.predict(x_test[0], (0, 0, 0)) # (0, 508, 0)

print('ANSWER: ', y_test[0])
# ! Last 8 nodes are packed incorrectly in first layer 87 != 174