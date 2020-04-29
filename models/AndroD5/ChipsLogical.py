# AUTHOR: Daniel Raymond
# DATE  : 2020-04-014
# ABOUT : Logical combinations that are a combination of multiple ICs

from ChipsAsync import pins, XNOR, bitAND, CHIP

# Uses XNOR to AND to turn on when signals are equivalent # ! Make purely python to increase efficiency
class Comparator(CHIP):
    def __init__(self, in_len, name=""):
        super(Comparator, self).__init__(1, name=name)
        self.in_width = in_len
        self.xnor_gate = XNOR(in_len, name=f"{name} - XNOR")
        and_gate = bitAND(in_len, name=f"{name} - AND")
        
        # Internal wiring
        and_gate.wire(self.xnor_gate.output)
        self.output.wire(and_gate.output)

    def wire(self, a, b):
        assert isinstance(a, pins) and isinstance(b, pins), f"[COMP]\t{self.name} inputs must be of type pin"
        assert a.width == self.in_width and b.width == self.in_width, f"[COMP]\t{self.name} input size expected to be {self.in_width}"
        self.xnor_gate.wire(a, b)
