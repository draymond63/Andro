# AUTHOR: Daniel Raymond
# DATE  : 2020-04-014
# ABOUT : Logical combinations that are a combination of multiple ICs


if __name__ == "__main__":
    from ChipsGen import pins, XNOR, AND, CHIP, GATE
else:
    # Package is in sim when it is not the main (Ignore error)
    from sim.ChipsGen import pins, XNOR, AND, CHIP, GATE

# Takes all of one signal and ANDs it together
class MultiAND(GATE):
    def __init__(self, in_len=2, name=""):
        super(MultiAND, self).__init__("mAND", self.expr, 1, name)
        self.in_width = in_len
    def expr(self, i):
        # Make sure all of input is on
        isAND = True
        for a in self.a.value:
            if not a: isAND = False
        return isAND

# Uses XNOR to AND to turn on when signals are equivalent
class COMPARE(CHIP):
    def __init__(self, in_len, name=""):
        super(COMPARE, self).__init__(1, name=name)
        self.in_width = in_len
        self.xnor_gate = XNOR(in_len, name=f"{name} - XNOR")
        self.and_gate = MultiAND(in_len, name=f"{name} - AND")
        
        # Internal wiring
        self.and_gate.wire(self.xnor_gate.output)
        self.output.wire(self.and_gate.output)

    def wire(self, a, b):
        assert isinstance(a, pins) and isinstance(b, pins), f"[COMP]\t{self.name} inputs must be of type pin"
        assert a.width == self.in_width and b.width == self.in_width, f"[COMP]\t{self.name} input size expected to be {self.in_width}"
        self.xnor_gate.wire(a, b)
