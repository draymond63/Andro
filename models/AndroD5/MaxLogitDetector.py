# AUTHOR: Daniel Raymond
# DATE  : 2020-04-29
# ABOUT : Determines the max value in the final layer and returns its index

import ChipsClocked as IC
import ChipsAsync as asyncIC
from tqdm import tqdm

class MaxLogitSelector():
    def __init__(self):
        self._initChips()
        self._initWiring()

    def _initChips(self):
        # EEPROM that stores the values
        self.FINAL_EEPROM = asyncIC.EEPROM(addr_len=7, name='EE-Data')
        # Index to iterate throught the logits
        self.index = IC.Counter(7, name='Index')
        # Flip flop to store the current macimum value seen and it's index (answer)
        self.max_val = IC.FlipFlop(8, name='Max-Val')
        self.max_index = IC.FlipFlop(7, name='Max-Index')
        # Compares current value to max_val, and loads it if it is higher (along with the index)
        self.val_comp = asyncIC.MagnitudeComparator(8, name='Val-Comp')
        self.is_greater = self.val_comp[0:1]
        # Clock (Increments index)
        self.clk = IC.CLOCK()
        # ! Know when to finish

    def _initWiring(self):
        # Make index/address increment on each cycle
        self.index.wire(self.clk)
        self.FINAL_EEPROM.wire(self.index.output)
        # Attach max registers to current, updating when value is greater
        self.max_index.wire(self.index.output, clk=self.is_greater) # ! NEEDS TO BE CALCULATED FIRST
        self.max_val.wire(self.FINAL_EEPROM.output, clk=self.is_greater)
        # Detect when current value is greater than max
        self.val_comp.wire(self.FINAL_EEPROM.output, self.max_val.output)

    def select(self, logits):
        num_logits = len(logits)
        # Load image
        self.FINAL_EEPROM.fill(logits)
        # Pulse clock
        while self.index.raw != num_logits:
            self.clk.pulse()

        return self.max_index.raw

img_logits = [118, 106, 110, 120, 120, 112, 100, 132, 106, 120]
s = MaxLogitSelector()
print('Answer:', s.select(img_logits))
