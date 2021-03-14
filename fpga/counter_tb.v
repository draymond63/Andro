`timescale 1ns/1ns
`include "counter.v"

module counter_tb;

parameter LEN = 5;

reg clk = 0;
reg reset = 0;
wire [LEN - 1:0] count;
wire ovf;

counter #(.DATA_WIDTH(LEN)) out (clk, reset, count, ovf);

initial begin
	$dumpfile("counter_tb.vcd");
	$dumpvars(0, counter_tb);

	for (integer i = 0; i < 100; i++) begin
		clk ^= 1;
		#20;
	end
	reset = 1;
	for (integer i = 0; i < 100; i++) begin
		clk ^= 1;
		#20;
		reset = 0;
	end
	$display("Test Complete");
end

endmodule