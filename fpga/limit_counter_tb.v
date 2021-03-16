`timescale 1ns/1ns
`include "limit_counter.v"

module limit_counter_tb;
	reg clk = 0;
	reg [7:0] limit = 'hF;

	limit_counter #(.COUNT_WIDTH(8)) count (
		.clk(clk),
		.limit(limit)
	);

	initial begin
		$dumpfile("limit_counter_tb.vcd");
		$dumpvars(0, limit_counter_tb);

		for (integer i = 0; i < 70; i++) begin
			clk ^= 1;
			#1;
		end
		$display("Test Complete");
	end

endmodule