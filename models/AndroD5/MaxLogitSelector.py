# AUTHOR: Daniel Raymond
# DATE  : 2020-04-29
# ABOUT : Determines the max value in the final layer and returns its index

import ChipsClocked as IC
import ChipsAsync as asyncIC
from tqdm import tqdm

class MaxLogitSelector():
    def __init__(self, EE_addr_width, EE_io_width, name='Max-Logit-Sel'):
        self.is_wired = False
        self.name = name
        self._initChips(EE_addr_width, EE_io_width)
        self._initWiring()

    def _initChips(self, EE_addr_width, EE_io_width):
        # Clock (Increments index)
        self.clk = IC.CLOCK()
        # EEPROM that stores the values
        self.FINAL_EEPROM = asyncIC.EEPROM(addr_len=EE_addr_width, io_len=EE_io_width, name='MLS EE-Data')
        # Index to iterate throught the logits
        self.index = IC.Counter(EE_addr_width, name='MLS Index')
        # Flip flop to store the current macimum value seen and it's index (answer)
        self.max_val = IC.FlipFlop(EE_io_width, name='MLS Max-Val')
        self.max_index = IC.FlipFlop(EE_addr_width, name='MLS Max-Index')
        # Compares current value to max_val, and loads it if it is higher (along with the index)
        self.val_comp = asyncIC.MagnitudeComparator(EE_io_width, name='MLS Val-Comp')
        self.is_greater = self.val_comp[0:1]
        # Trigger clock pins
        self.trig_clk = asyncIC.AND(name='MLS Trig-Clk')
        self.trigger = asyncIC.pins(val=1, name='MLS Def-Trigger')
        # ! Know when to finish

    def _initWiring(self):
        # Make index/address increment on each cycle
        self.index.wire(self.trig_clk.output)
        self.FINAL_EEPROM.wire(self.index.output)
        # Attach max registers to current, updating when value is greater
        self.max_index.wire(self.index.output, clk=self.is_greater) # * NEEDS TO BE CALCULATED FIRST
        self.max_val.wire(self.FINAL_EEPROM.output, clk=self.is_greater)
        # Detect when current value is greater than max
        self.val_comp.wire(self.FINAL_EEPROM.output, self.max_val.output)
        self.trig_clk.wire(self.clk.output)
        self.trig_clk.wire(self.clk.output, self.trigger)

    def select(self, logits=None):
        assert logits or self.is_wired, "Select must be given logits or wired"
        if self.is_wired:
            num_logits = self.size.raw
        else:
            num_logits = len(logits)
            # Load image if required
            self.FINAL_EEPROM.fill(logits)
        # Pulse clock
        while self.index.raw != num_logits:
            self.clk.pulse()
        # Return value if it is wanted
        # print('Answer:', self.max_index.raw)
        return self.max_index.raw

    def wire(self, EEPROM, trigger, size, clk):
        self.is_wired = True
        assert isinstance(EEPROM, asyncIC.EEPROM), f"[EEPROM]\t{self.name} must be given an EEPROM for the data"
        assert isinstance(trigger, asyncIC.pins), f"[EEPROM]\t{self.name} trigger must be driven by pins"
        assert isinstance(size, asyncIC.pins), f"[EEPROM]\t{self.name} size must be driven by pins"
        assert isinstance(clk, IC.CLOCK), f"[EEPROM]\t{self.name} clk must be a CLOCK object"
        assert trigger.width == 1, f"[EEPROM]\t{self.name} needs 1 pin for trigger, but got {trigger.width}"
        # Run the program when trigger goes high
        trigger.register_callback(lambda: self.select() if trigger.raw else None)
        # Unwire (Just for efficiency)
        self.index.unwire_output()
        self.FINAL_EEPROM.unwire_output()
        self.max_index.unwire_output()
        self.max_val.unwire_output()
        self.trig_clk.unwire_output()
        # Resave references
        self.FINAL_EEPROM = EEPROM
        self.trigger = trigger
        self.size = size
        self.clk = clk
        # Rewire
        self._initWiring()

# img_logits = [118, 106, 110, 120, 120, 112, 100, 132, 106, 120]
# EEPROM = asyncIC.EEPROM(7, name='EEPROM')
# EEPROM.fill(img_logits)

# trig = asyncIC.pins(name='Trigger')
# size = asyncIC.pins(4, val=10, name='LAYER_SIZE')
# clk = IC.CLOCK()

# s = MaxLogitSelector(EE_addr_width=7, EE_io_width=8)
# s.wire(EEPROM, trig, size, clk)

# for _ in range(1000): # Clock is still activating
#     clk.pulse()

# trig.value = 1
