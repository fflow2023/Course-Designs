`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: e
// Engineer: 
// 
// Create Date: 2025/11/20 16:31:52
// Design Name: 
// Module Name: ex_mem
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


module ex_mem(
    input clk,
    input [31:0]ex_wdata0,
    input [4:0]ex_wd0,
    input ex_wreg0,
    output reg[31:0]mem_data,
    output reg[4:0]mem_wd,
    output reg mem_wreg,
    input exDelay_i,
    output reg memDelay_o,
    input [1:0]ex_lsop0,
    input [31:0]ex_memaddr,
    input [31:0]ex_reg20,
    output reg[1:0]mem_lsop,
    output reg[31:0]mem_memaddr,
    output reg[31:0]mem_reg2
    );
    always@(posedge clk)begin
        mem_data<=ex_wdata0;
        mem_wd<=ex_wd0;
        mem_wreg<=ex_wreg0;
        memDelay_o<=exDelay_i;
        mem_lsop<=ex_lsop0;
        mem_memaddr<=ex_memaddr;
        mem_reg2<=ex_reg20;
    end
    
endmodule
