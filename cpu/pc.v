`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/10/30 16:33:38
// Design Name: 
// Module Name: pc
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


module pc(
    input wire rst,clk,
    output reg ce,
    output reg [31:0] pc,
    input branchF,
    input [31:0]branchAddr
    );
    always@(posedge clk)begin
        if(rst==1)
            ce<=0;
        else
            ce<=1;
    end
    always@(posedge clk)begin
        if(ce==0)
            pc<=0;
        else if(branchF==1)
            pc<=branchAddr;
        else
            pc<=pc+4;
     end
     
endmodule
