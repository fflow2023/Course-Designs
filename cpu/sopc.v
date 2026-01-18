`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: h
// Engineer: 
// 
// Create Date: 2025/11/20 14:29:00
// Design Name: 
// Module Name: sopc
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


module sopc(
    input clk,rst
    );
    wire rom_ce_o;
    wire [31:0]rom_addr_o;
    wire [31:0]inst_i;
//    singlecycle_cpu cpu0(clk,rst,
    
    //decided bt pipeline_cpu
    wire[31:0]ram_addr_o;
    wire ram_ce_o;
    wire ram_we_o;
    wire[31:0]ram_data_i;
    wire[31:0]ram_data_o;
    pipeline_cpu cpu0(clk,rst,
    inst_i,rom_ce_o,rom_addr_o,ram_addr_o,
    ram_ce_o,ram_we_o,ram_data_i,ram_data_o);
    
    data_ram data_ram0(clk,ram_addr_o,ram_ce_o,ram_we_o,
    ram_data_i,ram_data_o);
    
    inst_rom inst_rom0(clk,rom_addr_o,
    rom_ce_o,inst_i);
    
    
endmodule
