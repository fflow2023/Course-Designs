`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/11/27 16:16:35
// Design Name: 
// Module Name: data_ram
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


module data_ram(
    input clk,
    input[31:0] addr,
    input ce,
    input we,
    input [31:0]data_i,
    output reg [31:0]data_o
    );
    reg[31:0] ram[7:0];
    always@(*)begin
        if(ce==1 && we==0)
            data_o<=ram[addr[31:2]];
        else
            data_o<=32'd0;
    end
    always@(posedge clk)begin
        if(ce==1&&we==1)
            ram[addr[31:2]]<=data_i;
    end
endmodule
