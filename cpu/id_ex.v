`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/11/20 16:27:26
// Design Name: 
// Module Name: id_ex
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


module id_ex(
    input clk,
    input[13:0]id_aluop,
    input[31:0]id_reg1,
    input[31:0]id_reg2,
    input[4:0]id_wd,
    input id_wreg,
    output reg[13:0]ex_aluop,
    output reg[31:0]ex_reg1,
    output reg[31:0]ex_reg2,
    output reg[4:0]ex_wd,
    output reg ex_wreg,
    input idDelay_i,
    input nexIsDelay_i,
    output reg exDelay_o,
    output reg isDelay_o,
    input [31:0]id_inst0,
    input [1:0]id_lsop,
    output reg[31:0]ex_inst,
    output reg[1:0]ex_lsop
    );
    always@(posedge clk)begin
        ex_aluop<=id_aluop;
        ex_reg1<=id_reg1;
        ex_reg2<=id_reg2;
        ex_wd<=id_wd;
        ex_wreg<=id_wreg;
        exDelay_o<=idDelay_i;
        isDelay_o<=nexIsDelay_i;
        ex_inst<=id_inst0;
        ex_lsop<=id_lsop;
    end

endmodule
