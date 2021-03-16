`timescale 1ns/1ns
`include "nn_counter.v"

module nn_counter_tb;
	reg clk = 0;

	nn_counter count (.clk(clk));

	initial begin
		$dumpfile("nn_counter_tb.vcd");
		$dumpvars(0, nn_counter_tb);

		while(!count.model_done) begin
			clk ^= 1;
			#1;
		end
		// for (integer i = 0; i < 1000; i++) begin
		// 	clk ^= 1;
		// 	#1;
		// end
		$display("Test Complete");
	end

endmodule