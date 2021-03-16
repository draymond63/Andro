module limit_counter #(parameter COUNT_WIDTH=8) (clk, limit, ovf);

	input clk;
	input wire [COUNT_WIDTH - 1:0] limit;
	output reg ovf = 0;

	reg [COUNT_WIDTH - 1:0] count = 0;

	always @(posedge clk) begin	
		ovf = 0;
		if (count == limit) begin
			count = 0;
			ovf = 1;
		end else begin
			count++;
		end
	end

endmodule