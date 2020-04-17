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
    def in_width(self):
        return self._in_width # By default, output matches input
    @raw.setter
    def raw(self, val):
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
        return f"{self.name}: {str(self.output)}"
    def __bool__(self):
        return bool(self.raw)

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
class NOT(GATE):
    def __init__(self, out_len=1, name=""):
        super(NOT, self).__init__("NOT", self.expr, out_len, name)
    def expr(self, i):
        return not self.a.value[i]

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

# ********************************** CLOCK DEFINITION
class CLOCK():
    def __init__(self, tethers=[]):
        self.state = 0
        self.output = pins(1)
        self._callbacks=[]
        for i in tethers:
            try:    self.sync(i.update)
            except: raise EnvironmentError(f"{i} does not have a function named update")

    def sync(self, obj):
        self._callbacks.append(lambda: obj.update() if self.state else None)

    def toggle(self):
        self.state ^= 1
        self.output.raw = self.state
        for callback in self._callbacks:
            callback()

    def pulse(self, times=1):
        for _ in range(2 * times):
            self.toggle()

    def __bool__(self):
        return bool(self.state)

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
