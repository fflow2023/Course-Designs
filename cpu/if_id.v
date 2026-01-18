`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/11/20 16:24:44
// Design Name: 
// Module Name: if_id
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module if_id(
    input clk,
    input [31:0]if_inst,
    output reg[31:0]id_inst,
    input [31:0] if_pc,
    output reg[31:0]id_pc
    );
    
    always@(posedge clk)begin
        id_inst<=if_inst;
        id_pc<=if_pc;
    end
endmodule
