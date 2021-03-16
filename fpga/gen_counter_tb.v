`timescale 1ns/1ns
`include "gen_counter.v"

module gen_counter_tb;

	parameter LEN = 5;

	reg clk = 0;
	reg reset = 0;
	wire [LEN - 1:0] count [0:1];
	wire ovf [0:1];

	gen_counter #(.DATA_WIDTH(LEN)) c_0 (clk, reset, count[0], ovf[0]);
	gen_counter #(.DATA_WIDTH(LEN - 1)) c_1 (clk, reset, count[1], ovf[1]);

	initial begin
		$dumpfile("gen_counter_tb.vcd");
		$dumpvars(0, gen_counter_tb);

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