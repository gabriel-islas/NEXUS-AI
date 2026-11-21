// SPDX-License-Identifier: Apache-2.0
// NEXUS-AI 8: signed int4 MAC with signed 8-bit saturating accumulator and ReLU.
// Dedicated 8-bit input bus; dedicated 8-bit result bus. No bidirectional GPIOs.
`default_nettype none
module tt_um_nexus_ai8 (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);
    // Input protocol: [7:6] command, [5] STB, [4] reserved, [3:0] int4.
    // 00 LOAD_X; 01 LOAD_W; 10 MAC; 11 CLEAR.
    // One command is accepted on each sampled STB rising edge.
    reg signed [3:0] x_reg;
    reg signed [3:0] w_reg;
    reg signed [7:0] acc;
    reg              stb_prev;

    wire signed [7:0] product = x_reg * w_reg;
    wire signed [8:0] extended_sum =
        $signed({acc[7], acc}) + $signed({product[7], product});
    wire signed [7:0] saturated_sum =
        (extended_sum > 9'sd127)  ? 8'sd127 :
        (extended_sum < -9'sd128) ? -8'sd128 : extended_sum[7:0];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            x_reg    <= 4'sd0;
            w_reg    <= 4'sd0;
            acc      <= 8'sd0;
            stb_prev <= 1'b0;
        end else begin
            // Update STB history on every clock to detect only rising edges.
            stb_prev <= ui_in[5];
            if (ena && ui_in[5] && !stb_prev) begin
                case (ui_in[7:6])
                    2'b00: x_reg <= $signed(ui_in[3:0]);
                    2'b01: w_reg <= $signed(ui_in[3:0]);
                    2'b10: acc   <= saturated_sum;
                    2'b11: begin
                        acc   <= 8'sd0;
                        x_reg <= 4'sd0;
                        w_reg <= 4'sd0;
                    end
                    default: acc <= acc;
                endcase
            end
        end
    end

    // ReLU: negative signed accumulator is displayed as zero.
    assign uo_out  = acc[7] ? 8'd0 : acc[7:0];
    assign uio_out = 8'b00000000;
    assign uio_oe  = 8'b00000000;
    wire _unused = &{uio_in, ui_in[4], 1'b0};
endmodule
`default_nettype wire
