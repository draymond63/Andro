# AUTHOR: Daniel Raymond
# DATE  : 2020-04-013
# ABOUT : Async pieces that all generations can use

# *********************************** PIN DEFINITIONS
class pins():
    def __init__(self, length, val=0, name=""):
        self._callbacks = []
        self.max_val = 2 ** length - 1
        self._value = [0] * length
        self._width = length

        self.value = val
        self.raw = 0
        self.name = name

    # Getters and Setters
    @property
    def width(self):
        return self._width
    @property
    def value(self):
        return self._value

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
        else:
            assert val <= self.max_val, f"[PIN]\t{self.name} expected value below {self.max_val}. Bit length: {self.width}"
            self.raw = val
            # Split bits into array
            for i in range(self.width):
                self._value[i] = 1 if val & (1 << i) else 0
        # Update every async object connected
        self._notify_observers()

    # Let all async objects update
    def _notify_observers(self):
        for callback in self._callbacks:
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

# *********************************** REG DEFINITIONS
# class register():
#     def __init__(self, bit_length, val=0, name=""):
#         self.val
#         self.output = pins(bit_length, val)

#     def update(self, val):
#         self.val = val
#         self.output.value = val


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
