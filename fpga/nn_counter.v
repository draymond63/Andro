`include "gen_counter.v"
`include "limit_counter.v"

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
	// Reset signals
	output wire node_done;
	output wire layer_done;
	output reg model_done = 0;

	// Stores the shape info about the neural network
	// ! SHOULD BE LOADED DYNAMICALLY
	reg [NODE_WIDTH - 1:0] shape_info [0:2**LAYER_WIDTH - 1];
	// Limits
	wire [WEIGHT_WIDTH - 1 : 0] node_max = shape_info[layers_counter.count] - 1;
	wire [NODE_WIDTH - 1 : 0] layer_max = shape_info[layers_counter.count + 1] - 1;;
 
	limit_counter #(.COUNT_WIDTH(WEIGHT_WIDTH)) weights_counter (
		.clk   (clk),
		.limit (node_max),
		.ovf   (node_done)
	);
	limit_counter #(.COUNT_WIDTH(NODE_WIDTH)) nodes_counter (
		.clk   (node_done),
		.limit (layer_max),
		.ovf   (layer_done)
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
		shape_info[4] = 6;
		shape_info[3] = 5;
		shape_info[2] = 4;
		shape_info[1] = 3;
		shape_info[0] = 2;
	end

	always @(posedge clk) begin
		if (shape_info[layers_counter.count + 1] == 0)
			model_done = 1;
		else
			model_done = 0;
	end
endmodule