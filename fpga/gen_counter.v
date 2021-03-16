module gen_counter #(parameter COUNT_WIDTH=8) (clk, reset, count, ovf);

	input clk;
	input reset;
	output reg [COUNT_WIDTH - 1:0] count = 0;
	output reg ovf = 0;

	always @(posedge clk) begin	
		ovf = 0;
		if (reset)
			count = 0;
		else begin
			count++;
			if (count == 0) ovf = 1;
		end
	end

endmodule