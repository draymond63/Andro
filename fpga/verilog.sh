cd C:/Users/dan/Desktop/Projects/Andro/fpga

echo "CREATING VVP FILE"
iverilog -o $1_tb.vvp $1_tb.v

echo "CREATING VCD FILE"
vvp $1_tb.vvp