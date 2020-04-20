# AUTHOR: Daniel Raymond
# DATE  : 2020-04-07
# ABOUT : Initial software implementation of all the chips used in the circuit - used in AndroD5

if __name__ == "__main__":
    from ChipsAsync import pins, CHIP
else:
    # Package is in sim when it is not the main (Ignore error)
    from sim.ChipsAsync import pins, CHIP

# ********************************** CLOCK-SYNCED BASE CLASS
class ClockedChip(CHIP):
    def __init__(self, out_len=8, val=0, name=""):
        super(ClockedChip, self).__init__(out_len=out_len, val=val, name=name)
        self._i_val = self.raw # Intermediate value

    # Setting of value & raw need to affect the intermediate value now
    @property
    def value(self):
        return self.output.value
    @property
    def raw(self):
        return self.output.raw
    @value.setter
    def value(self, val):
        self.output.value = val
        self._raw = self.output.raw
        self._i_val = self._raw
    @raw.setter
    def raw(self, val):
        assert isinstance(val, int), f"[CLKIC]\t{self.name} raw setter needs object of type int, not {type(val)}"
        self.output.value = val
        self._raw = val
        self._i_val = val

    def _calculate(self):
        raise OSError(f"[CLKIC]\t{self.name} object needs the _calculate function defined in order to be used")

    def _display(self):
        assert self._i_val <= self.max_val, f"[CLKIC]\t{self.name} has calculated intermediate value that exceeds maximum of {self.max_val}, but got {self._i_val}"
        self.value = self._i_val

    def update(self):
        self._calculate()
        self._display()

# ********************************** CLOCK-SYNCED IC DEFINITIONS
# Accumulator for node math
class UpDownCounter(ClockedChip):
    # Connect incoming signals to the chip
    def wire(self, up_down, clk=None):
        assert isinstance(up_down, pins), "[UPDWN]\tCounter must be driven by pins"
        assert up_down.width == 1, f"[UPDWN]\tCounter only needs one bit of input, not {up_down.width}"
        # Create input pins
        self.up_down = up_down
        # Optional clock
        if isinstance(clk, pins):
            assert clk.width == 1, f"[UPDWN]\t{self.name} clock must be 1 bit, not {clk.width}"
            self.clk = clk
            clk.register_callback(lambda: self.update() if self.clk.raw else None)
        elif isinstance(clk, CLOCK):
            clk.sync(self)
        elif clk is not None:
            raise AssertionError(f"[UPDWN]\t{self.name} clock must a clock or pins object, not {type(clk)}")

    def _calculate(self):
        try:
            self._i_val += 1 if self.up_down else -1
            self.value = self._i_val # Update array in value
        except AttributeError:
            AttributeError(f"[UPDWN]\t{self.name} has not been wired, but an update has been triggered (FLOATING INPUT)")

# Increments with update/clk
class Counter(ClockedChip):
    def __init__(self, out_len=8, val=0, name=""):
        super(Counter, self).__init__(out_len=out_len, val=val, name=name)
        self.reset = None # Initialize data_in

    def wire(self, load=None, reset=None, clk=None):
        # Reset config
        if isinstance(reset, pins):
            assert isinstance(load, pins), f"[COUNT]\t{self.name} load must be a pins object, not {type(load)}"
            self.load = load
            self.reset = reset
        elif reset is not None:
            raise AssertionError(f"[COUNT]\t{self.name} reset must be a pins object, not {type(reset)}")
        # Clock config
        if isinstance(clk, pins):
            assert clk.width == 1, f"[COUNT]\t{self.name} clock must be 1 bit, not {clk.width}"
            self.clk = clk
            clk.register_callback(lambda: self.update() if self.clk.raw else None)
        elif isinstance(clk, CLOCK):
            clk.sync(self)
        elif clk is not None:
            raise AssertionError(f"[COUNT]\t{self.name} clock must a clock or pins object, not {type(clk)}")

    # Increment counter or load value
    def _calculate(self):
        if self.reset:
            self._i_val = self.load.raw
        else:
            self._i_val = self._i_val + 1

# ? D1 Needs latch
class ShiftRegister(ClockedChip):
    # Wire inputs
    def wire(self, data, clk=None):
        assert isinstance(data, pins), f"[SREG]\t{self.name} must be driven by pins"
        assert data.width == 1, f"[SREG]\t{self.name} requires 1 bit of serial data, not {data.width}"
        self.data = data
        if isinstance(clk, pins):
            assert clk.width == 1, f"[SREG]\t{self.name} clock must be 1 bit, not {clk.width}"
            self.clk = clk
            clk.register_callback(lambda: self.update() if self.clk.raw else None)
        elif isinstance(clk, CLOCK):
            clk.sync(self)
        elif clk is not None:
            raise AssertionError(f"[SREG]\t{self.name} clock must a clock or pins object, not {type(clk)}")

    def _calculate(self):
        # Shift in data
        _raw = self.raw << 1
        _raw = _raw | self.data.raw # Take the input
        # Ignore overflow
        self._i_val = _raw % (1 << self.width)

class FlipFlop(ClockedChip):
    def __init__(self, out_len=8, val=0, name=""):
        super(FlipFlop, self).__init__(out_len=out_len, val=val, name=name)
        self.data_in = None # Initialize data_in

    def wire(self, data_in, clk=None):
        assert isinstance(data_in, pins), f"[FLFP]\t{self.name} must be driven by pins"
        assert data_in.width == self.width, f"[FLFP]\t{self.name} requires {self.width} input(s), not {data_in.width}"
        self.data_in = data_in
        # If a clock is given, make it update automatically
        if isinstance(clk, pins):
            assert clk.width == 1, f"[FLFP]\t{self.name} clock must be 1 bit, not {clk.width}"
            self.clk = clk
            clk.register_callback(lambda: self.update() if self.clk.raw else None)
        elif isinstance(clk, CLOCK):
            clk.sync(self)
        elif clk is not None:
            raise AssertionError(f"[FLFP]\t{self.name} clock must a clock or pins object, not {type(clk)}")
            

    def _calculate(self):
        if self.data_in is None:
            raise AssertionError(f"[FLFP]\t{self.name} updated with floating input")
        self._i_val = self.data_in.raw


# ********************************** CLOCK DEFINITION
# Calculates all objects outputs, then display all values so that it doesn't matter what order objects are tethered in
class CLOCK():
    def __init__(self, tethers=[]):
        self.state = 0
        self.output = pins(1)
        self.synced_objects=[]
        for obj in tethers:
            try:    self.sync(obj)
            except: raise AssertionError(f"{obj} does not have a function named update")

    def sync(self, obj):
        if isinstance(obj, list):
            for i in obj:
                self.synced_objects.append(i)
        # Otherwise just sync the one
        else:
            self.synced_objects.append(obj)

    def toggle(self):
        self.state ^= 1
        self.output.raw = self.state
        # On rising edge
        if self.state:
            # Calculate the future values of all the clock-synced chips
            for obj in self.synced_objects:
                if isinstance(obj, ClockedChip):
                    obj._calculate()
            # Display their values
            for obj in self.synced_objects:
                if isinstance(obj, ClockedChip):
                    obj._display()
                else:
                    obj.update()

    def pulse(self, times=1):
        for _ in range(2 * times):
            self.toggle()

    def __bool__(self):
        return bool(self.state)

