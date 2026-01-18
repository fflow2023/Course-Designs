`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/10/30 16:33:53
// Design Name: 
// Module Name: regfile
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


module regfile(
    input wire re1,
    input wire[4:0]raddr1,
    input wire re2,
    input wire[4:0]raddr2,
    input wire[4:0]waddr,
    input wire we,
    input wire[31:0]wdata,
    input wire rst,
    input wire clk,
    output reg[31:0]rdata1,
    output reg[31:0]rdata2
    );
    reg[31:0]regs[31:0];
    always@(posedge clk)begin
        if(rst==0 && we==1 && waddr!=0)
            regs[waddr]<=wdata;
    end
    always@(*)begin
        if(rst==1)
            rdata1<=0;
        else if(rst==0 && re1==1 && raddr1==0)
            rdata1<=0;
        else if((rst==0) && (re1==1) &&(we==1) &&(raddr1==waddr))
            rdata1<=wdata;
        else if(rst==0 && re1==1)
            rdata1<=regs[raddr1];
        else rdata1<=0;
    end
    always@(*)begin
        if(rst==1)
            rdata2<=0;
        else if(rst==0 && re2==1 && raddr2==0)
            rdata2<=0;
        else if((rst==0) && (re2==1) &&(we==1) &&(raddr2==waddr))
            rdata2<=wdata;
        else if(rst==0 && re2==1)
            rdata2<=regs[raddr2];
        else rdata2<=0;
    end
endmodule
