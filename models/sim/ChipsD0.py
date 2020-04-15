# AUTHOR: Daniel Raymond
# DATE  : 2020-04-07
# ABOUT : Initial software implementation of all the chips used in the circuit - used in AndroD5

if __name__ == "__main__":
    from ChipsGen import pins, CHIP, CLOCK
else:
    # Package is in sim when it is not the main (Ignore error)
    from sim.ChipsGen import pins, CHIP, CLOCK

# ? D1 needs to have i/o pins together
# EEPROM
class EEPROM(CHIP):
    # Define output pins and constants
    def __init__(self, addr_len=12, io_len=8, name=""):
        super(EEPROM, self).__init__(io_len, name=name)
        self.size = (1 << addr_len) - 1 # Measured in bits
        self.data = [0] * (self.size + 1)
        self.addr_width = addr_len
        self.isWriting = 0 # Initially ground rd_wr -> set to read

    @property
    def value(self):
        return self.output.value
    @property
    def raw(self):
        return self.output.raw

    # Define input pins
    def wire(self, addr, data_in=None, rd_wr=None, flash=None):
        # Make sure they are pins
        assert isinstance(addr, pins), f"[EEPROM]\t{self.name} must be driven by pins"
        # Make sure they are the correct widths
        assert addr.width == self.addr_width, f"[EEPROM]\t{self.name} needs {self.addr_width} address pins, but got {addr.width}"
        # Listen to input pins
        addr.register_callback(self.display)
        self.addr = addr # Create input pin references
        self.display() # Initially display the data

        # Optional input
        if data_in != None:
            assert isinstance(data_in, pins), f"[EEPROM]\t{self.name} must be driven by pins"
            assert isinstance(rd_wr, pins), f"[EEPROM]\t{self.name} must be driven by pins"
            assert isinstance(flash, pins), f"[EEPROM]\t{self.name} must be driven by pins"
            assert data_in.width == self.in_width, f"[EEPROM]\t{self.name} needs {self.in_width} input pins, but got {data_in.width}"
            assert rd_wr.width == 1, f"[EEPROM]\t{self.name} needs 1 pin for rd/wr, but got {rd_wr.width}"
            assert flash.width == 1, f"[EEPROM]\t{self.name} needs 1 pin for flash, but got {flash.width}"
            rd_wr.register_callback(self._updateWr) # Listen to read/write
            flash.register_callback(self.update) # Listen to flash
            self.data_in = data_in
            self.flash = flash
            self.rd_wr = flash

    # * Assumes data is three dimensional - LAYER : NODE : WEIGHT
    def fill3D(self, data, addr_bits_per_dim):
        assert len(addr_bits_per_dim) == 3,  f"[EEPROM]\t{self.name} fill3D requires data is 3 dimensional"
        assert sum(addr_bits_per_dim) <= self.addr_width,  f"[EEPROM]\t{self.name} addr width {self.addr_width} does not match those given to fill3D()"
        # Get enough memory to pad out with zeroes
        self.data = [0] * (1 << self.addr_width) # ? EEPROMS generally store 0xFF as default, not 0
        
        layer_size = 1 << addr_bits_per_dim[1]
        weight_size = 1 << addr_bits_per_dim[2]
        emptyNode = [0] * weight_size     

        # Pad data with zeros
        for layer in data:
            # Extend nodes to be same length as weight size
            for node in layer:
                node.extend( [0] * (weight_size - len(node)) )
            # Make enough dummy nodes to pad out layer
            layer.extend( [emptyNode] * (layer_size - len(layer)) ) 

        # Iterate through data and linearize it
        index = 0
        for layer in data:
            for node in layer:
                for eight_weights in node:
                    self.data[index] = eight_weights
                    index += 1
    
    def display(self):
        if self.isWriting:
            self.output.value = 0
        else:
            assert self.addr.raw < len(self.data), f"[EEPROM]\t{self.name} Address lines achieved a value of {self.addr.raw}, when max is {len(self.data)}"
            self.output.value = self.data[self.addr.raw]

    def _updateWr(self):
        self.isWriting = self.rd_wr.raw
    def update(self):
        if self.isWriting:
            self.data[self.addr.raw] = self.data_in.raw
        else:
            raise EnvironmentError(f"[EEPROM]\t{self.name} tried to write to EEPROM with rd_wr pin set to {self.rd_wr.raw}")

# Accumulator for node math
class UpDownCounter(CHIP):
    # Connect incoming signals to the chip
    def wire(self, up_down):
        assert isinstance(up_down, pins), "[UPDWN]\tCounter must be driven by pins"
        assert up_down.width == 1, f"[UPDWN]\tCounter only needs one bit of input, not {up_down.width}"
        # Create input pins
        self.up_down = up_down
        # * Listener is to the clock, not the input pins
        # clk.register_callback(self.update)

    def update(self):
        self.raw = self.raw + 1 if self.up_down.raw else self.raw - 1
        self.value = self.raw # Update array in value

# Increments with update/clk
class Counter(CHIP):
    # ? Useless with clock module
    def wire(self, clk):
        assert isinstance(clk, pins), "[COUNT]\tCounter must be driven by pins"
        assert clk.width == 1, f"[COUNT]\tCounter only needs one bit of input, not {clk.width}"
        # * Listen when the clock pulses on
        if type(clk) == pins:
            assert clk.width == 1, f"[SREG]\t{self.name} clock must be 1 bit, not {clk.width}"
            self.clk = clk
            clk.register_callback(lambda: self.update() if self.clk.raw else None)
        elif type(clk) == CLOCK:
            clk.sync(self)
    # Increment counter
    def update(self):
        self.raw = self.raw + 1

# ? D1 Needs latch and clock
class ShiftRegister(CHIP):
    # Wire inputs
    def wire(self, data, clk=None):
        assert isinstance(data, pins), f"[SREG]\t{self.name} must be driven by pins"
        assert data.width == 1, f"[SREG]\t{self.name} requires 1 bit of serial data, not {data.width}"
        self.data = data
        if type(clk) == pins:
            assert clk.width == 1, f"[SREG]\t{self.name} clock must be 1 bit, not {clk.width}"
            self.clk = clk
            clk.register_callback(lambda: self.update() if self.clk.raw else None)
        elif type(clk) == CLOCK:
            clk.sync(self)

    def update(self):
        # Shift in data
        self.raw = self.raw + 1
        self.raw = self.raw | self.data.raw
        # Ignore overflow
        self.raw = self.raw % (1 << self.width)

class FlipFlop(CHIP):
    def wire(self, data_in, clk=None):
        assert isinstance(data_in, pins), f"[FLFP]\t{self.name} must be driven by pins"
        assert data_in.width == self.width, f"[FLFP]\t{self.name} requires {self.width} input(s), not {data_in.width}"
        self.data_in = data_in
        # If a clock is given, make it update automatically
        if type(clk) == pins:
            assert clk.width == 1, f"[SREG]\t{self.name} clock must be 1 bit, not {clk.width}"
            self.clk = clk
            clk.register_callback(lambda: self.update() if self.clk.raw else None)
        elif type(clk) == CLOCK:
            clk.sync(self)

    def update(self):
        self.value = self.data_in.value
