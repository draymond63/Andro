cd C:/Users/dan/Desktop/Projects/Andro/fpga

echo "  -  Compiling:"
iverilog -o $1_tb.vvp $1_tb.v

if [ $? -eq 0 ]
then
	echo "  -  Starting Simulation:"
	vvp $1_tb.vvp
	echo "  -  Ending Simulation"
fi
