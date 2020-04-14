# AUTHOR: Daniel Raymond
# DATE  : 2020-04-013
# ABOUT : Async pieces that all generations can use

# *********************************** PIN DEFINITIONS
class pins():
    def __init__(self, length, val=0, name=""):
        self.name = name
        self._callbacks = []
        self.max_val = 2 ** length - 1
        self._value = [0] * length
        self._width = length

        self.value = val
        self.raw = 0

    # Getters and Setters
    @property
    def width(self):
        return self._width
    @property
    def value(self):
        return self._value

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

    # Functions
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
            self.raw = raw >> 1
        # If value given is a raw value
        elif isinstance(val, int):
            assert val <= self.max_val, f"[PIN]\t{self.name} expected value below {self.max_val}. Bit length: {self.width}"
            self.raw = val
            # Split bits into array
            for i in range(self.width):
                self._value[i] = 1 if val & (1 << i) else 0
        else:
            raise TypeError(f"{val} is of type {type(val)}, not list or int")
        # Update every async object connected
        self._notify_observers()

    # Let all async objects update
    def _notify_observers(self):
        for callback in self._callbacks:
            try: # Try and pass the value if it is needed
                callback(self)
            except:
                callback()
    def register_callback(self, callback):
        self._callbacks.append(callback)

# ********************************** GATE DEFINITIONS
# XNOR gate
class Multiplier():
    def __init__(self, name=""):
        self.output = pins(1, name=f"{name} - Output")

    @property
    def value(self):
        return self.output.value

    # Connect incoming signals to the chip
    def wire(self, a, b):
        assert isinstance(a, pins) and isinstance(b, pins), "[XNOR]\tMultiplier must be driven by two output pins"
        assert a.width == 1 and b.width == 1, "[XNOR]\tMultiplier can only handle 1 bit operations"
        # Listen to both inputs
        a.register_callback(self.mult)
        b.register_callback(self.mult)
        self.a = a
        self.b = b
        self.mult() # Run the initial multiplication

    def mult(self):
        val = 1 if self.a.value == self.b.value else 0
        self.raw = val
        self.output.value = val

# ********************************** ASYNC IC DEFINITIONS
# Selector (Generally used in conjunction with EEPROM)
class Multiplexor():
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
    
    def select(self):
        # Get appropriate range
        sel_rng = (self.sel.raw, self.sel.raw+self.out_len)
        # Parse input and put it into output directly (as a list)
        self.output.value = self.a.value[sel_rng[0]:sel_rng[1]]


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
