# AUTHOR: Daniel Raymond
# DATE  : 2020-04-013
# ABOUT : Async pieces that all generations can use

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
        return f"{self.name}: {string}"
    # * SLICE
    def __getitem__(self, k):
        # Avoid divide by zero error
        step = k.step if k.step else 1
        assert (k.stop-k.start)//step > 0, f"[PIN]\t{self.name} Improper slice"
        # Create new set of pins
        temp_pins = pins( (k.stop-k.start)//step, name=f"{self.name}[{k.start}:{k.stop}:{step}]" )
        temp_pins.start = k.start
        temp_pins.end = k.stop
        temp_pins.step = step
        # Force new pins to update with current ones
        self.register_callback(temp_pins._force_update)
        temp_pins._force_update(self)
        return temp_pins

    # * Only used with __getitem__
    def _force_update(self, input_pin):
        if self.step <= 0:  self.value = input_pin.value[ self.start:self.end - 1:self.step ]
        else:               self.value = input_pin.value[ self.start:self.end    :self.step ]

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
            assert val <= self.max_val, f"[PIN]\t{self.name} expected value below {self.max_val}. Bit length: {self.width}"
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
            try: # Try and pass the value if it is needed
                callback(self)
            except:
                callback()
    def register_callback(self, callback):
        self._callbacks.append(callback)

# *********************************** CHIP BASE DEFINITION
class CHIP():
    def __init__(self, out_len=8, name=""):
        self.name = name
        self._raw = 0
        self._value = 0
        self.output = pins(out_len, name=f"{name} - Output")

    @property
    def value(self):
        return self.output.value
    @property
    def raw(self):
        return self.output.raw
    @property
    def width(self):
        return self.output.width
    @raw.setter
    def raw(self, val):
        self.output.value = val
        self._raw = val
    @value.setter
    def value(self, val):
        self.output.value = val
        self._raw = self.output.raw

    def __str__(self):
        return str(self.output)

# ********************************** GATE DEFINITIONS
class GATE(CHIP):
    # Init is built off CHIP
    def __init__(self, gate_name, expression, out_len, name=""):
        super(GATE, self).__init__(out_len=out_len)
        self.gate_name = gate_name
        self.expression = expression
    # Connect incoming signals to the chip
    def wire(self, a, b):
        assert isinstance(a, pins) and isinstance(b, pins), f"[{self.gate_name}]\t{self.name} must be driven by two output pins"
        assert a.width == self.width and b.width == self.width, f"[{self.gate_name}]\t{self.name} inputs must be the same size as the ouput: {self.width}"
        # Listen to both inputs
        a.register_callback(self.calc)
        b.register_callback(self.calc)
        self.a = a
        self.b = b
        self.calc() # Run the initial multiplication
    # Run the expression to compute output
    def calc(self):
        temp = []
        for i in range(self.width):
            if self.expression(i):  temp.append(1)
            else:                   temp.append(0)
        self.value = temp

class XNOR(GATE):
    def __init__(self, out_len=1, name=""):
        super(XNOR, self).__init__("XNOR", self.expr, out_len, name)
    def expr(self, i):
        return self.a.value[i] == self.b.value[i]

class AND(GATE):
    def __init__(self, out_len=1, name=""):
        super(AND, self).__init__("AND", self.expr, out_len, name)
    def expr(self, i):
        return self.a.value[i] and self.b.value[i]

# ********************************** ASYNC IC DEFINITIONS
# Selector (Generally used in conjunction with EEPROM)
class Multiplexor(CHIP):
    def __init__(self, out_len=1, name=""):
        self.output = pins(out_len, name=f"{name} - Output")
        self.out_len = out_len
        self.name = name

    # Return value of output pin if requested
    @property
    def value(self):
        return self.output.value
    @property
    def raw(self):
        return self.output.raw

    # Define input pins
    def wire(self, a, sel):
        assert a.width == self.out_len << sel.width, f"[MUX]\t{self.name} pin dimensions don't match: {a.width} != {self.out_len} << {sel.width}"
        # Save dimensions
        self.in_len = a.width
        self.sel_len = sel.width
        # Multiplexor is async so always update with inputes
        a.register_callback(self.select)
        sel.register_callback(self.select)
        self.a = a
        self.sel = sel
        self.select() # Initialize state
    
    def select(self):
        # Get appropriate range
        sel_rng = (self.sel.raw, self.sel.raw+self.out_len)
        # Parse input and put it into output directly (as a list)
        self.output.value = self.a.value[sel_rng[0]:sel_rng[1]]

# ********************************** CLOCK DEFINITION
class CLOCK():
    def __init__(self, tethers=[]):
        self.state = 0
        self._callbacks=[]
        for i in tethers:
            try:    self.sync(i.update)
            except: raise EnvironmentError(f"{i} does not have a function named update")

    def sync(self, callback):
        self._callbacks.append(lambda: callback() if self.state else None)

    def toggle(self):
        self.state ^= 1
        for callback in self._callbacks:
            callback()

    def pulse(self, times=1):
        for _ in range(2 * times):
            self.toggle()

# o1 = pins(1)
# o2 = pins(2)
# mult = Multiplier()
# mult.wire(o1, o2)

# print(o1.value, o2.value, mult.value)
# o1.value = 1
# print(o1.value, o2.value, mult.value)
# o2.value = 1
# print(o1.value, o2.value, mult.value)
# o1.value = 0
# print(o1.value, o2.value, mult.value)
# o2.value = 0
# print(o1.value, o2.value, mult.value)
