`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: n
// Engineer: 
// 
// Create Date: 2025/11/13 14:29:48
// Design Name: 
// Module Name: decoder_5_32
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


module decoder_5_32(
    input[4:0] in,
    output[31:0] out
    );
    generate
        genvar i;
        for(i=0;i<32;i=i+1)begin:g1
            assign out[i]=(in==i);
        end
    endgenerate
        
endmodule
