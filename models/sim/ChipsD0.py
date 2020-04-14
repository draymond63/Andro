# AUTHOR: Daniel Raymond
# DATE  : 2020-04-07
# ABOUT : Initial software implementation of all the chips used in the circuit - used in AndroD5

if __name__ == "__main__":
    from ChipsGen import pins, Multiplier
else:
    # Package is in sim when it is not the main (Ignore error)
    from sim.ChipsGen import pins, CHIP

# ? D1 needs to have i/o pins together
# EEPROM
class EEPROM(CHIP):
    # Define output pins and constants
    def __init__(self, addr_len=12, io_len=8, name=""):
        self.name = name
        self.size = (1 << addr_len) - 1 # Measured in bits
        self.addr_width = addr_len
        self.isWriting = 0 # Initially ground rd_wr -> set to read
        self.output = pins(io_len, name=f"{name} - IO")

    @property
    def value(self):
        return self.output.value
    @property
    def raw(self):
        return self.output.raw

    # Define input pins
    def wire(self, addr, data_in=None, rd_wr=None):
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
            assert data_in.width == self.output.width, f"[EEPROM]\t{self.name} needs {self.output.width} input pins, but got {data_in.width}"
            assert rd_wr.width == 1, f"[EEPROM]\t{self.name} needs 1 pin for rd/wr, but got {rd_wr.width}"
            rd_wr.register_callback(self._updateWr) # Listen to read/write
            self.data_in = data_in
            self.rd_wr = data_in

    # * Assumes data is three dimensional - LAYER : NODE : WEIGHT
    def fill3D(self, data, addr_bits_per_dim):  
        assert len(addr_bits_per_dim) == 3,  f"[EEPROM]\t{self.name} fill3D requires data is 3 dimensional"
        assert sum(addr_bits_per_dim) == self.addr_width,  f"[EEPROM]\t{self.name} addr width {self.addr_width} does not match those given to fill()"
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
    def wire(self, clk):
        assert isinstance(clk, pins), "[COUNT]\tCounter must be driven by pins"
        assert clk.width == 1, f"[COUNT]\tCounter only needs one bit of input, not {clk.width}"
        # * Listen when the clock pulses on
        self.clk = clk
        clk.register_callback(lambda: self.update()) # if self.clk.raw else None
    # Increment counter
    def update(self):
        self.raw = self.raw + 1

# ? D1 Needs latch and clock
class ShiftRegister(CHIP):
    # Wire inputs
    def wire(self, data):
        assert isinstance(data, pins), "[SREG]\tShift Register must be driven by pins"
        assert data.width == 1, f"[UPDWN]\tShift Register requires 1 bit of serial data, not {data.width}"
        self.data = data

    def update(self):
        # Shift in data
        self.raw = self.raw + 1
        self.raw = self.raw | self.data.raw
        # Ignore overflow
        self.raw = self.raw % (1 << self.output.width)

class FlipFlop(CHIP):
    def wire(self, data_in):
        pass