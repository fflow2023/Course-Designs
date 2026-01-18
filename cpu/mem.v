`timescale 1ns / 1ps
`include "D:/Xilinx/FPGA/SY7/SY7.srcs/sources_1/imports/7/defines.v"

//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/11/20 16:21:25
// Design Name: 
// Module Name: mem
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


module mem(
    input [31:0]wdata_i,
    input [4:0]wd_i,
    input wreg_i,
    output [31:0]wdata_o,
    output [4:0]wd_o,
    output wreg_o,
    input isDelay_i,
    output is_Delay_o1,
    input [1:0]lsop_i,
    input [31:0]memaddr_i,
    input [31:0]reg2_i,
    input [31:0]mem_data_i,
    output [31:0]memaddr_o,
    output memwe_o,
    output memce_o,
    output [31:0]memdata_o
    );
    assign memaddr_o=memaddr_i;
    assign memwe_o=(lsop_i==`sw_op);
    assign memce_o=((lsop_i==`sw_op)||(lsop_i==`lw_op));
    assign memdata_o=reg2_i;
    assign wdata_o=(lsop_i==`lw_op)?mem_data_i:wdata_i;
    assign wd_o=wd_i;
    assign wreg_o=wreg_i;
    assign is_Delay_o1=isDelay_i;
endmodule