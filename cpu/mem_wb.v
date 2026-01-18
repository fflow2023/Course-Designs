`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: u
// Engineer: 
// 
// Create Date: 2025/11/20 16:34:28
// Design Name: 
// Module Name: mem_wb
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


module mem_wb(
    input clk,
    input wire[31:0]mem_wdata0,
    input wire[4:0]mem_wd0,
    input wire mem_wreg0,
    output reg[31:0]wb_wdata,
    output reg[4:0]wb_wd,
    output reg wb_wreg
    );
    always@(posedge clk)begin
        wb_wdata<=mem_wdata0;
        wb_wd<=mem_wd0;
        wb_wreg<=mem_wreg0;
    end
    
endmodule
