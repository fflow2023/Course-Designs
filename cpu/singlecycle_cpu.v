`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: q
// Engineer: 
// 
// Create Date: 2025/11/20 14:31:01
// Design Name: 
// Module Name: singlecycle_cpu
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


module singlecycle_cpu(
    input clk,rst,
    input [31:0]rom_inst_i,
    output rom_ce_o,
    output [31:0]rom_addr_o
    );
    pc pc0(rst,clk,rom_ce_o,rom_addr_o);
    wire [31:0]reg1_data;
    wire [31:0]reg2_data;
    wire reg1_read;
    wire [4:0]reg1_addr;
    wire reg2_read;
    wire [4:0]reg2_addr;
    wire id_wreg_o;
    wire [4:0]id_wd_o;
    wire [31:0]id_reg2_o;
    wire [31:0]id_reg1_o;
    wire [13:0]id_aluop_o;
    id id0(rom_inst_i,reg1_data,reg2_data,
    id_aluop_o,id_reg1_o,id_reg2_o,id_wd_o,
    id_wreg_o,reg2_addr,reg2_read,reg1_addr,reg1_read);
    wire ex_wreg;
    wire [4:0]ex_wd;
    wire [31:0]ex_wdata_o;
    alu alu0(id_aluop_o,id_reg1_o,id_reg2_o,
    id_wd_o,id_wreg_o,ex_wdata_o,ex_wd,ex_wreg);
    regfile regfile0(reg1_read,reg1_addr,
    reg2_read,reg2_addr,ex_wd,ex_wreg,
    ex_wdata_o,rst,clk,reg1_data,
    reg2_data);
    
endmodule
