`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/11/20 16:38:59
// Design Name: 
// Module Name: pipeline_cpu
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


module pipeline_cpu(
    input clk,rst,
    input [31:0]rom_inst_i,
    output rom_ce_o,
    output [31:0]rom_addr_o,
    output [31:0]ram_addr_o,
    output ram_ce_o,
    output ram_we_o,
    output [31:0] ram_data_i,
    input [31:0]ram_data_o
    );
    //decided by pc
    wire branchF;
    wire [31:0]branchAddr;
    pc pc0(rst,clk,rom_ce_o,rom_addr_o,branchF,branchAddr);
    wire[31:0]id_inst;
    //decided by if_id
    wire [31:0]id_pc;
    if_id if_id0(clk,rom_inst_i,id_inst,rom_addr_o,id_pc);
    //decided by regfile
    wire re1;
    wire[4:0]raddr1;
    wire re2;
    wire[4:0]raddr2;
    wire[31:0]rdata1;
    wire[31:0]rdata2;
    regfile regfile0(re1,raddr1,re2,raddr2,
    wb_wd,wb_wreg,wb_wdata,rst,clk,
    rdata1,rdata2);
    
    id id0(id_inst,rdata1,rdata2,
    id_aluop,id_reg1,id_reg2,id_wd,
    id_wreg,raddr2,re2,raddr1,re1,id_pc,
    isDelay_o,idDelay_i,nexIsDelay_i,
    branchF,branchAddr,id_inst0,id_lsop,mem_wdata0,mem_wd0,mem_wreg0,ex_wdata0,ex_wd0,
    ex_wreg0); 
    
    //decided by id_ex
    wire[13:0]id_aluop;
    wire[31:0]id_reg1;
    wire[31:0]id_reg2;
    wire[4:0]id_wd;
    wire id_wreg;
    wire[13:0]ex_aluop;
    wire[31:0]ex_reg1;
    wire[31:0]ex_reg2;
    wire[4:0]ex_wd;
    wire ex_wreg;
    wire idDelay_i;
    wire nexIsDelay_i;
    wire exDelay_o;
    wire isDelay_o;
    wire [31:0]id_inst0;
    wire [1:0]id_lsop;
    wire [31:0]ex_inst;
    wire [1:0]ex_lsop;

    id_ex id_ex0(clk,id_aluop,
    id_reg1,id_reg2,id_wd,id_wreg,
    ex_aluop,ex_reg1,ex_reg2,ex_wd,ex_wreg,
    idDelay_i,nexIsDelay_i,exDelay_o,isDelay_o,
    id_inst0,id_lsop,ex_inst,ex_lsop);
    
    alu alu0(ex_aluop,ex_reg1,ex_reg2,ex_wd,
    ex_wreg,ex_wdata0,ex_wd0,ex_wreg0,
    exDelay_o,exDelay_i,ex_inst,ex_lsop,
    ex_lsop0,ex_memaddr,ex_reg20);
    
    //decided by ex_mem
    wire[31:0]ex_wdata0;
    wire[4:0]ex_wd0;
    wire ex_wreg0;
    wire[31:0]mem_data;
    wire[4:0]mem_wd;
    wire mem_wreg;
    wire exDelay_i;
    wire memDelay_o;
    wire [1:0]ex_lsop0;
    wire [31:0]ex_memaddr;
    wire [31:0]ex_reg20;
    wire [1:0]mem_lsop;
    wire [31:0]mem_memaddr;
    wire [31:0]mem_reg2;
    
    ex_mem ex_mem0(clk,ex_wdata0,ex_wd0,
    ex_wreg0,mem_data,mem_wd,mem_wreg,
    exDelay_i,memDelay_o,ex_lsop0,ex_memaddr,
    ex_reg20,mem_lsop,mem_memaddr,mem_reg2);
    
    //decided by mem
    wire isDelay_o1;
    
    mem mem0(mem_data,mem_wd,mem_wreg,
        mem_wdata0,mem_wd0,mem_wreg0,memDelay_o,isDelay_o1,
        mem_lsop,mem_memaddr,mem_reg2,ram_data_o,ram_addr_o,
        ram_we_o,ram_ce_o,ram_data_i);

    //decide by mem_wb   
    wire[31:0]mem_wdata0;
    wire[4:0]mem_wd0;
    wire mem_wreg0;
    wire[31:0]wb_wdata;
    wire[4:0]wb_wd;
    wire wb_wreg;
    mem_wb mem_wb0(clk,mem_wdata0,mem_wd0,
    mem_wreg0,wb_wdata,wb_wd,wb_wreg);
    
endmodule