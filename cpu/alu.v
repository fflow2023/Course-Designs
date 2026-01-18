`timescale 1ns / 1ps
`include "D:/Xilinx/FPGA/SY7/SY7.srcs/sources_1/imports/7/defines.v"

//////////////////////////////////////////////////////////////////////////////////
// Company: z
// Engineer: 
// 
// Create Date: 2025/11/13 16:13:30
// Design Name: 
// Module Name: alu
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


module alu(
    input[13:0] alu_control,
    input[31:0] alu_src1,
    input[31:0] alu_src2,
    input [4:0] wd_i,
    input wreg_i,
    output[31:0]alu_result,
    output[4:0] wd_o,
    output wreg_o,
    input isDelay_i,
    output isDelay_o,
    input [31:0]inst_i,
    input [1:0]lsop_i,
    output [1:0]lsop_o,
    output [31:0]memaddr_o,
    output [31:0]reg2_o
    );
    assign lsop_o=lsop_i;
    assign reg2_o=alu_src2;
    assign memaddr_o={{16{inst_i[15]}},inst_i[15:0]}
    +alu_src1;
    
    assign isDelay_o=isDelay_i;
    
    
    assign wd_o=wd_i;
    assign wreg_o=wreg_i;
    wire[31:0]add_sub_result;
    wire[31:0]slt_result;
    wire[31:0]sltu_result;    
    wire[31:0]and_result;
    wire[31:0]or_result;
    wire[31:0]xor_result;
    wire[31:0]nor_result;
    wire[31:0]sll_result;
    wire[31:0]srl_result;
    wire[31:0]sra_result;
    wire[31:0]lui_result;
    
    assign add_sub_result = alu_src1+((alu_control == `add_op || alu_control == `addu_op) ? 
                             alu_src2 : -alu_src2);
    assign slt_result = ($signed(alu_src1) < $signed(alu_src2)) ? 1 : 0;
    assign sltu_result = (alu_src1 < alu_src2) ? 1 : 0;
    assign and_result = alu_src1 & alu_src2;
    assign or_result = alu_src1 | alu_src2;
    assign xor_result = alu_src1 ^ alu_src2;
    assign nor_result = ~(alu_src1 | alu_src2);
    assign sll_result = alu_src2 << alu_src1[4:0];
    assign srl_result = alu_src2 >> alu_src1[4:0];
    assign sra_result = $signed(alu_src2) >>> alu_src1[4:0];
    assign lui_result = alu_src1;
    
    assign alu_result=(alu_control==`add_op||alu_control==`addu_op||alu_control==`sub_op||alu_control==`subu_op)?add_sub_result:
    (alu_control==`slt_op)?slt_result:
    (alu_control==`sltu_op)?sltu_result:
    (alu_control==`and_op)?and_result:
    (alu_control==`or_op)?or_result:
    (alu_control==`xor_op)?xor_result:
    (alu_control==`nor_op)?nor_result:
    (alu_control==`sll_op)?sll_result:
    (alu_control==`srl_op)?srl_result:
    (alu_control==`sra_op)?sra_result:
    (alu_control==`lui_op)?lui_result:
    32'b0;
    
endmodule
