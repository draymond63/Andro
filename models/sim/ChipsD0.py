# AUTHOR: Daniel Raymond
# DATE  : 2020-04-07
# ABOUT : Initial software implementation of all the chips used in the circuit - used in AndroD5

from ChipsGen import pins, Multiplier

# EEPROM
class EEPROM():
    # Define output pins and constants
    def __init__(self, addr_len=12, io_len=8, name=""):
        self.name = name
        self.size = (1 << addr_len) - 1 # Measured in bits
        self.addr_width = addr_len
        self.io_pins = pins(io_len, name=f"{name} - IO")

    # Define input pins
    def wire_addr(self, addr):
        assert isinstance(addr, pins), f"[EEPROM]\t{self.name} must be driven by pins"
        assert addr.width == self.addr_width, f"[EEPROM]\t{self.name} needs {self.addr_width} pins, but got {addr.width}"
        addr.register_callback(self.display)
        # Create input pin references
        self.addr_pins = addr
        self.display()

    # * Assumes data is three dimensional - LAYER : NODE : WEIGHT
    def fill3D(self, data, addr_bits_per_dim):  
        assert len(addr_bits_per_dim) == 3,  f"[EEPROM]\t{self.name} fill3D requires data is 3 dimensional"
        assert sum(addr_bits_per_dim) == self.addr_width,  f"[EEPROM]\t{self.name} addr width {self.addr_width} does not match those given to fill()"
        # Get enough memory to pad out with zeroes
        self.data = [0] * (1 << self.addr_width) # ! EEPROMS generally store 0xFF as default, not 0
        
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
        self.io_pins.value = self.data[self.addr_pins.raw]

# Selector (Generally used in conjunction with EEPROM)
class Multiplexor():
    def __init(self, out_length=1):
        self.out_len = out_length

# Accumulator for node math
class UpDownCounter():
    def __init__(self, length=8, name=""):
        self.output = pins(length, name=f"{name} - Output")
        self.raw = 0

    # Getter
    @property
    def value(self):
        return self.output.value
    # Setter
    @value.setter
    def value(self, val):
        self.output.value = val

    # Connect incoming signals to the chip
    def wire(self, up_down):
        assert isinstance(up_down, pins), "[UPDWN]\tCounter must be driven by pins"
        assert up_down.width == 1, "[UPDWN]\tCounter only needs one bit of input"
        # Create input pins
        self.up_down = up_down
        # Listen to both inputs # * Listener is to the clock, not the input pins
        # up_down.register_callback(self.update)

    def update(self):
        self.raw = self.raw + 1 if self.up_down.raw else self.raw - 1
        self.value = self.raw # Update array in value


# Test to see that xnor + adder work
weights = [0, 1, 0, 1]
inputs = [0, 0, 1, 1]

w_pin = pins(1)
i_pin = pins(1)

xnor = Multiplier(name="XNOR")
xnor.wire(w_pin, i_pin)

accum = UpDownCounter(name="accum")
accum.wire(xnor.output)

for w, i in zip(weights, inputs):
    w_pin.value = w
    i_pin.value = i
    accum.update()
    print(xnor.raw, ":", accum.raw)
