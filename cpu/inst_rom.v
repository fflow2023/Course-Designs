`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/11/06 16:12:17
// Design Name: 
// Module Name: inst_rom
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


module inst_rom(
    input clk,
    input wire[31:0] addr,
    input wire ce,
    output reg[31:0]inst
    );
    reg[31:0] rom[127:0];    
    initial begin
        $readmemh("D:/Xilinx/FPGA/SY7/inst_rom12.data",rom);
    end

    always@(*)begin
        if(ce==1)
            inst<=rom[addr>>2];
        else
            inst<=0;
    end
    
endmodule
