# NEXUS-AI 8

NEXUS-AI 8 is a compact, signed 4-bit multiply-accumulate datapath with an 8-bit signed saturating accumulator and a ReLU output. Designed for **one 1x1 Tiny Tapeout GlobalFoundries tile** (fit must be confirmed by the GDS build).

## Inputs

Only `ui_in[7:0]` is used:

* `ui_in[7:6]`: command (`00` load X, `01` load W, `10` MAC, `11` clear)
* `ui_in[5]`: command strobe, sampled on rising edge
* `ui_in[4]`: reserved
* `ui_in[3:0]`: signed int4 operand

**Dedicated signals:** `clk`, active-low `rst_n`, `ena`. `uio` are not used and are disabled.

## Outputs

`uo_out[7:0]` continuously displays `max(0, saturate8(acc + x*w + ...))` (from 0 to 127). Arithmetic is performed on the strobe edge. For example, load X=3, W=2 and issue MAC twice: output progresses 0 → 6 → 12. Negative results are shown as zero due to ReLU.

See the repository README for the control protocol and step-by-step tests.
