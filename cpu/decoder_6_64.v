`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/11/13 14:34:17
// Design Name: 
// Module Name: decoder_6_64
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


module decoder_6_64(
    input[5:0] in,
    output[63:0] out
    );
    generate
        genvar i;
        for(i=0;i<64;i=i+1)begin:g1
            assign out[i]=(in==i);
        end
    endgenerate
    
endmodule
