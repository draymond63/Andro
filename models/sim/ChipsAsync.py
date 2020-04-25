# AUTHOR: Daniel Raymond
# DATE  : 2020-04-013
# ABOUT : Async pieces that all generations can use

from inspect import signature

# *********************************** PIN DEFINITION
class pins():
    def __init__(self, length=1, val=0, pins_list=None, name=""):
        # Permanent attributes
        self.name = name
        self._callbacks = []
        self._raw = 0
        # Default Constructor
        if pins_list == None:
            self.max_val = 2 ** length - 1
            self._value = [0] * length
            self._width = length
            self.value = val
        # Packing Constructor
        else:
            # * List of pins if from least significant group to most
            self.pins_list = pins_list
            self._width = sum(pin.width for pin in pins_list)
            self._value = [0] * self.width
            self.max_val = 2 ** self.width - 1

            for pins_sel in pins_list:
                assert isinstance(pins_sel, pins), f"[PINS]\t{self.name} pins_list must only contain pins objects, not {type(pins_sel)}"
                pins_sel.register_callback(self._updateGroup)

            self._updateGroup()

    # Getters and Setters
    @property
    def width(self):
        return self._width
    @property
    def value(self):
        return self._value
    @property
    def raw(self):
        return self._raw

    # * PRINT
    def __str__(self):
        string = ''
        for bit in self.value:
            string += str(bit)
        string = string[::-1]
        return f"{string}"
    # * SLICE
    def __getitem__(self, k):
        # Avoid divide by zero error
        step = k.step if k.step else 1
        assert step == 1 or step == -1, f"[PIN]\t{self.name} Pins only support steps of either -1 or 1, not {step}"
        # Allows for empty positions in the slice
        if k.start is None: start = 0 if step == 1 else self.width
        else: start = k.start
        if k.stop is None: stop = 0 if step == -1 else self.width
        else: stop = k.stop
        # Create new set of pins
        _sliced_pins = pins( abs(stop-start), name=f"{self.name}[{start}:{stop}:{step}]" )
        _sliced_pins.start = start
        _sliced_pins.stop = stop
        _sliced_pins.step = step
        # Force new pins to update with current ones
        self.register_callback(_sliced_pins._force_update)
        _sliced_pins._force_update(self)
        return _sliced_pins
    # * BOOL
    def __bool__(self):
        return bool(self.raw)

    # * Only used with __getitem__
    def _force_update(self, input_pin):
        if self.width == input_pin.width: 
            self.value = input_pin.value[::-1]
        elif self.step <= 0: 
            self.value = input_pin.value[ self.start:self.stop - 1:self.step ]
        else:
            self.value = input_pin.value[ self.start:self.stop    :self.step ]

    # Setters
    @raw.setter
    def raw(self, val):
        self.value = val
    @value.setter
    def value(self, val):
        # If value given is a list of bits
        if isinstance(val, list):
            assert len(val) == self.width, f"[PIN]\t{self.name} expected input of {self.width} bits, but got {len(val)}"
            self._value = val
            # Pack bits into number for raw
            raw = 0
            for i in val[::-1]:
                raw |= i
                raw <<= 1
            self._raw = raw >> 1
        # If value given is a raw value
        elif isinstance(val, int):
            assert val <= self.max_val, f"[PIN]\t{self.name} expected value below {self.max_val}, but got {val}"
            self._raw = val
            # Split bits into array
            for i in range(self.width):
                self._value[i] = 1 if val & (1 << i) else 0
        else:
            raise TypeError(f"{val} is of type {type(val)}, not list or int")
        # Update every async object connected
        self._notify_observers()

    def _updateGroup(self):
        temp = []
        # Iterate through input pins
        for pin_group in self.pins_list:
            temp.extend( pin_group.value )
        self.value = temp

    # Let all async objects update
    def _notify_observers(self):
        for callback in self._callbacks:
            # If the callback needs a parameter
            if len(signature(callback).parameters) == 1:
                callback(self)
            else:
                callback()

    def register_callback(self, callback):
        self._callbacks.append(callback)

    # Wire pin to listen to input 'a'
    def wire(self, a):
        assert isinstance(a, pins), f"[PIN]\t{self.name} must have 'a' be an pin"
        assert a.width == self.width , f"[PIN]\t{self.name} input is size {a.width} when expected {self.width}"
        def _update():
            self.value = a.value
        a._callbacks.append(_update)

# *********************************** CHIP BASE DEFINITION
class CHIP():
    def __init__(self, out_len=8, val=0, name=""):
        self.name = name
        self._raw = 0
        self._value = 0
        self._in_width = out_len
        self.output = pins(out_len, val=val, name=name)

    @property
    def value(self):
        return self.output.value
    @property
    def raw(self):
        return self.output.raw
    @property
    def width(self):
        return self.output.width
    @property
    def max_val(self):
        return self.output.max_val
    @property
    def in_width(self):
        return self._in_width # By default, output matches input
    @raw.setter
    def raw(self, val):
        assert isinstance(val, int), f"[GENIC]\t{self.name} raw setter needs object of type int, not {type(val)}"
        self.output.value = val
        self._raw = val
    @value.setter
    def value(self, val):
        self.output.value = val
        self._raw = self.output.raw
    @in_width.setter
    def in_width(self, val):
        self._in_width = val

    def __str__(self):
        return f"{self.name}: {self.output}"
    def __bool__(self):
        return bool(self.raw)
    # * SLICE
    def __getitem__(self, k):
        _sliced_pins = self.output.__getitem__(k)
        return _sliced_pins

# ********************************** GATE DEFINITIONS
class GATE(CHIP):
    # Init is built off CHIP
    def __init__(self, gate_name, expression, out_len, name=""):
        super(GATE, self).__init__(out_len=out_len, name=name)
        self.gate_name = gate_name
        self.expression = expression
    # Connect incoming signals to the chip
    def wire(self, a, b=None):
        assert isinstance(a, pins), f"[{self.gate_name}]\t{self.name} must have 'a' be a pin"
        assert a.width == self.in_width , f"[{self.gate_name}]\t{self.name} input a is size {a.width} when chip expected {self.in_width}"
        a.register_callback(self.calc)
        self.a = a
        # Listen to both inputs if they exist
        if b != None:
            assert isinstance(b, pins), f"[{self.gate_name}]\t{self.name} must have 'b' be a pin"
            assert b.width == self.in_width, f"[{self.gate_name}]\t{self.name} input b is size {a.width} when chip expected {self.in_width}"
            b.register_callback(self.calc)
            self.b = b
        self.calc() # Run the initial multiplication
    # Run the expression to compute output
    def calc(self):
        temp = []
        for i in range(self.width):
            if self.expression(i):  temp.append(1)
            else:                   temp.append(0)
        self.value = temp

class XOR(GATE):
    def __init__(self, out_len=1, name=""):
        super(XOR, self).__init__("XOR", self.expr, out_len, name)
    def expr(self, i):
        return self.a.value[i] != self.b.value[i]
class AND(GATE):
    def __init__(self, out_len=1, name=""):
        super(AND, self).__init__("AND", self.expr, out_len, name)
    def expr(self, i):
        return self.a.value[i] and self.b.value[i]
class OR(GATE):
    def __init__(self, out_len=1, name=""):
        super(OR, self).__init__("OR", self.expr, out_len, name)
    def expr(self, i):
        return self.a.value[i] or self.b.value[i]
# * NOTTED VERSIONS
class NOT(GATE):
    def __init__(self, out_len=1, name=""):
        super(NOT, self).__init__("NOT", self.expr, out_len, name)
    def expr(self, i):
        return not self.a.value[i]
class XNOR(GATE):
    def __init__(self, out_len=1, name=""):
        super(XNOR, self).__init__("XNOR", self.expr, out_len, name)
    def expr(self, i):
        return self.a.value[i] == self.b.value[i]
class NAND(GATE):
    def __init__(self, out_len=1, name=""):
        super(NAND, self).__init__("NAND", self.expr, out_len, name)
    def expr(self, i):
        return not (self.a.value[i] and self.b.value[i])
class NOR(GATE):
    def __init__(self, out_len=1, name=""):
        super(NOR, self).__init__("NOR", self.expr, out_len, name)
    def expr(self, i):
        return not (self.a.value[i] or self.b.value[i])

# * SINGLE INPUT GATES
class bitGate(GATE):
    def __init__(self, gate_name, expression, in_len, name=""):
        super(bitGate, self).__init__(gate_name, expression, 1, name)
        self.in_width = in_len
class bitAnd(bitGate):
    def __init__(self, in_len=1, name=""):
        super(bitAnd, self).__init__("bAND", self.expr, in_len, name)
    def expr(self, i):
        # Make sure all of input is on
        for a in self.a.value:
            if not a: # If anything is not on, AND is off
                return False
        return True
class bitNOR(bitGate):
    def __init__(self, in_len=1, name=""):
        super(bitNOR, self).__init__("bNOR", self.expr, in_len, name)
    def expr(self, i):
        # Make sure all of input is on
        for a in self.a.value:
            if a: # If anything is on, NOR is off
                return False
        return True
class bitOR(bitGate):
    def __init__(self, in_len=1, name=""):
        super(bitOR, self).__init__("bOR", self.expr, in_len, name)
    def expr(self, i):
        # Make sure all of input is on
        for a in self.a.value:
            if a: # If anything is on, NOR is off
                return True
        return False

# ********************************** ASYNC IC DEFINITIONS
# Selects one bit out of the input (Generally used in conjunction with EEPROM)
class bitMux(CHIP):
    def __init__(self, name=""):
        self.name = name
        self._raw = 0
        self._value = 0
        self._in_width = 1
        self.output = pins(1, name=name)
    # Define input pins
    def wire(self, a, sel):
        assert a.width == 1 << sel.width, f"[MUX]\t{self.name} pin dimensions don't match: {a.width} != 1 << {sel.width}"
        # Save dimensions
        self.in_len = a.width
        self.sel_len = sel.width
        # Multiplexor is async so always update with inputes
        a.register_callback(self.select)
        sel.register_callback(self.select)
        self.a = a
        self.sel = sel
        self.select() # Initialize state
    # Parse input and put it into output directly (as a list)
    def select(self):
        self.value = self.a.value[self.sel.raw:self.sel.raw+1]

# Choose between two different inputs
class Mux(CHIP):
    # Define input pins
    def wire(self, a, b, sel):
        assert a.width <= self.in_width, f"[MUX]\t{self.name} pin dimensions don't match: {a.width} != {self.in_width}"
        assert b.width <= self.in_width, f"[MUX]\t{self.name} pin dimensions don't match: {b.width} != {self.in_width}"
        assert sel.width == 1, f"[MUX]\t{self.name} select pin must be a width of 1"
        # Save dimensions
        self.in_len = a.width
        # Multiplexor is async so always update with inputs
        a.register_callback(self.select)
        b.register_callback(self.select)
        sel.register_callback(self.select)
        self.a = a
        self.b = b
        self.sel = sel
        self.select() # Initialize state
    
    def select(self):
        # Allows widths less than output width (HW: the other inputs need to be grounded)
        if self.sel:
            self.raw = self.b.raw
        else:
            self.raw = self.a.raw



# ******************************************************** EEPROM DEFINITION
# ? D1 needs to have i/o pins together
class EEPROM(CHIP):
    # Define output pins and constants
    def __init__(self, addr_len=12, io_len=8, name=""):
        super(EEPROM, self).__init__(io_len, name=name)
        self.max_addr = (1 << addr_len) - 1 # Measured in bits
        self.data = [0] * (self.max_addr + 1) # ? EEPROMS generally store 0xFF as default, not 0
        self.addr_width = addr_len
        self.rd_wr = 0

    def binData(self, start, end):
        string = f'{self.name}: '
        for el in self.data[start:end]:
            string += format(el, '#010b')
            string += '\t'
        return string

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
            flash.register_callback(self.update) # Listen to flash
            # Save pins
            self.data_in = data_in
            self.flash = flash
            self.rd_wr = rd_wr

    # * Assumes data is three dimensional - LAYER : NODE : WEIGHT
    def fill3D(self, data, addr_bits_per_dim):
        assert len(addr_bits_per_dim) == 3,  f"[EEPROM]\t{self.name} fill3D requires data is 3 dimensional"
        assert sum(addr_bits_per_dim) <= self.addr_width,  f"[EEPROM]\t{self.name} addr width {self.addr_width} does not match those given to fill3D()"
        
        layer_size = 1 << addr_bits_per_dim[1]
        weight_size = 1 << addr_bits_per_dim[2]
        emptyNode = [0] * weight_size # Doesn't matter that this is pass by reference since all the values are getting inserted into self.data  

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
        if self.rd_wr:
            self.output.value = 0
        else:
            assert self.addr.raw < len(self.data), f"[EEPROM]\t{self.name} Address lines achieved a value of {self.addr.raw}, when max is {len(self.data)}"
            self.output.value = self.data[self.addr.raw]

    def update(self):
        if self.flash and self.rd_wr:
            # print(f"FLASHING {self.name} with {self.data_in} at {self.addr.raw}")
            self.data[self.addr.raw] = self.data_in.raw