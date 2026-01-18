`timescale 1ns / 1ps
`include "D:/Xilinx/FPGA/SY7/SY7.srcs/sources_1/imports/7/defines.v"
//////////////////////////////////////////////////////////////////////////////////
// Company: j
// Engineer: 
// 
// Create Date: 2025/11/13 14:16:24
// Design Name: 
// Module Name: id
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


module id(
    input [31:0]inst_i,
    input [31:0]reg1_data_i,
    input [31:0]reg2_data_i,
    output [13:0]aluop_o,
    output [31:0]reg1_o,
    output [31:0]reg2_o,
    output [4:0]wd_o,
    output wreg_o,
    output [4:0]reg2_addr_o,
    output reg2_read_o,
    output [4:0]reg1_addr_o,
    output reg1_read_o,
    input [31:0]pc_i,
    input isDelay_i,
    output isDelay_o,
    output nextIsDelay_o,
    output branchF_o,
    output [31:0]branchAddr_o,
    output [31:0]inst_o,
    output [1:0]lsop_o,
    
    input [31:0]memwdata_b,
    input [4:0]memwd_b,
    input memwreg_b,
    input [31:0]exwdata_b,
    input [4:0]exwd_b,
    input exwreg_b
    );
    //add by lw sw
    assign inst_o=inst_i;
    assign isDelay_o=isDelay_i;
    
    wire [5:0]func;
    wire [63:0]func_d;
    wire [4:0]sa;
    wire [31:0]sa_d;
    wire [4:0]op1;
    wire [31:0]op1_d;
    wire [5:0]op;
    wire [63:0]op_d;
    assign func = inst_i[5:0];
    assign sa = inst_i[10:6];
    assign op1 = inst_i[25:21];
    assign op = inst_i[31:26];
    decoder_6_64 d0(func,func_d);
    decoder_5_32 d1(sa,sa_d);
    decoder_5_32 d2(op1,op1_d);
    decoder_6_64 d3(op,op_d);
    wire inst_add;
    wire inst_addu;
    wire inst_sub;
    wire inst_subu;
    wire inst_slt;
    wire inst_sltu;
    wire inst_and;
    wire inst_or;
    wire inst_xor;
    wire inst_nor;
    wire inst_sll;
    wire inst_srl;
    wire inst_sra;
    wire inst_lui;
    //add at 9
    wire inst_beq;
    wire inst_bne;
    //add at 10
    wire inst_lw;
    wire inst_sw;
    assign inst_add=op_d[0] && sa_d[0] && func_d[`func_add];
    assign inst_addu=op_d[0] && sa_d[0] && func_d[`func_addu];
    assign inst_sub=op_d[0] && sa_d[0] && func_d[`func_sub];
    assign inst_subu=op_d[0] && sa_d[0] && func_d[`func_subu];
    assign inst_slt=op_d[0] && sa_d[0] && func_d[`func_slt];
    assign inst_sltu=op_d[0] && sa_d[0] && func_d[`func_sltu];
    assign inst_and=op_d[0] && sa_d[0] && func_d[`func_and];
    assign inst_or=op_d[0] && sa_d[0] && func_d[`func_or];
    assign inst_xor=op_d[0] && sa_d[0] && func_d[`func_xor];
    assign inst_nor=op_d[0] && sa_d[0] && func_d[`func_nor];
    assign inst_sll=op_d[0] && op1_d[0] && func_d[`func_sll];
    assign inst_srl=op_d[0] && op1_d[0] && func_d[`func_srl];
    assign inst_sra=op_d[0] && op1_d[0] && func_d[`func_sra];
    assign inst_lui=op_d[`op_lui]&&op1_d[0];
    //add at 9
    assign inst_beq=op_d[`op_beq];
    assign inst_bne=op_d[`op_bne];
    //add at 10
    assign inst_lw=op_d[`op_lw];
    assign inst_sw=op_d[`op_sw];
    assign lsop_o={inst_lw,inst_sw};
    assign aluop_o={
        inst_add,inst_addu,inst_sub,inst_subu,
        inst_slt,inst_sltu,inst_and,inst_or,
        inst_xor,inst_nor,inst_sll,inst_srl,
        inst_sra,inst_lui
    };
    assign wd_o=(inst_lui||inst_lw)?inst_i[20:16]:inst_i[15:11];
    assign wreg_o=!(inst_beq||inst_bne||inst_sw);
    assign reg2_addr_o=inst_i[20:16];
    assign reg2_read_o=!(inst_lui||inst_lw);
    assign reg1_addr_o=inst_i[25:21];
    assign reg1_read_o=!(inst_sll || inst_srl || inst_sra || inst_lui);
    wire[31:0] imm;
    assign imm=inst_lui?{inst_i[15:0],16'b0}:{27'b0,inst_i[10:6]};
    assign reg1_o=reg1_read_o?reg1_mux:imm;
    assign reg2_o=reg2_read_o?reg2_mux:imm;
    //add at 9
    assign nextIsDelay_o=(inst_beq||inst_bne);
    assign branchF_o=(inst_beq)?(
        (reg1_mux==reg2_mux)?1:0
    ):(
        (inst_bne)?(
            (reg1_mux!=reg2_mux)?1:0    
        ):0
    ); 
    assign branchAddr_o={{14{inst_i[15]}},inst_i[15:0],2'b00}
    +pc_i+4;
    
    // memwdata_b exwdata_b reg1_data_i
    wire [31:0]reg1_mux;
    wire [31:0]reg2_mux;
    assign reg1_mux=((reg1_read_o==1)&&(exwreg_b==1)&&(exwd_b==reg1_addr_o)
    )?(exwdata_b):
    (((reg1_read_o==1)&&(memwreg_b==1)&&(memwd_b==reg1_addr_o))?(memwdata_b):(
    (reg1_read_o==1)?reg1_data_i:32'b0)
    );
    assign reg2_mux=((reg2_read_o==1)&&(exwreg_b==1)&&(exwd_b==reg2_addr_o)
    )?(exwdata_b):
    (((reg2_read_o==1)&&(memwreg_b==1)&&(memwd_b==reg2_addr_o))?(memwdata_b):(
    (reg2_read_o==1)?reg2_data_i:32'b0)
    );
    
endmodule
