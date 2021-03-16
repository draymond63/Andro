`include "gen_counter.v"

module nn_counter (
	clk,
	node_done,
	layer_done,
	model_done,
	mem_select
);	
	parameter LOGIT_NUM = 10;
	localparam WEIGHT_WIDTH = 8;
	localparam NODE_WIDTH = 8;
	localparam LAYER_WIDTH = 3;

	input clk;
	output wire mem_select;

	// Stores the shape info about the neural network
	// ! SHOULD BE LOADED DYNAMICALLY
	reg [NODE_WIDTH - 1:0] shape_info [0:2**LAYER_WIDTH - 1];
	// Reset signals
	output reg node_done = 0;
	output reg layer_done = 0;
	output reg model_done = 0;
 
	gen_counter #(.COUNT_WIDTH(WEIGHT_WIDTH)) weights_counter (
		.clk   (clk),
		.reset (node_done)
	);
	gen_counter #(.COUNT_WIDTH(NODE_WIDTH)) nodes_counter (
		.clk   (node_done),
		.reset (layer_done) // ! RESET ISN'T HAPPENING
	);
	gen_counter #(.COUNT_WIDTH(LAYER_WIDTH)) layers_counter (
		.clk   (layer_done),
		.reset (1'b0)
	);

	assign mem_select = layers_counter.count[0];

	// ! REPLACE WITH FILE READ
	initial begin
		shape_info[6] = 0;
		shape_info[5] = LOGIT_NUM;
		shape_info[4] = 7;
		shape_info[3] = 3;
		shape_info[2] = 8;
		shape_info[1] = 2;
		shape_info[0] = 9;
	end

	always @(posedge clk) begin
		if (weights_counter.count >= shape_info[layers_counter.count])
			node_done = 1;
		else
			node_done = 0;

		if (nodes_counter.count >= shape_info[layers_counter.count + 1])
			layer_done = 1;
		else
			layer_done = 0;

		if (shape_info[layers_counter.count + 1] == 0)
			model_done = 1;
		else
			model_done = 0;
	end
endmodule