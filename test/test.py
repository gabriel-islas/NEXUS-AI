# SPDX-License-Identifier: Apache-2.0
"""Cocotb 2.x tests: run with `cd test && make` (Icarus required)."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, Timer

LOAD_X, LOAD_W, MAC, CLEAR = 0, 1, 2, 3

async def command(dut, op, value=0):
    """Generate STB low-high-low, clocked by clk."""
    await FallingEdge(dut.clk)
    dut.ui_in.value = (op << 6) | (value & 15)
    await ClockCycles(dut.clk, 2)
    await FallingEdge(dut.clk)
    dut.ui_in.value = (op << 6) | 0x20 | (value & 15)
    await ClockCycles(dut.clk, 2)
    await Timer(1, unit="ns")
    await FallingEdge(dut.clk)
    dut.ui_in.value = (op << 6) | (value & 15)
    await ClockCycles(dut.clk, 1)

async def assert_result(dut, value):
    await Timer(1, unit="ns")
    actual = int(dut.uo_out.value)
    assert actual == value, f"expected {value}, got {actual}"
    assert int(dut.uio_oe.value) == 0
    assert int(dut.uio_out.value) == 0

@cocotb.test()
async def test_mac_relu_saturation_and_strobe(dut):
    dut.clk.value = 0
    dut.rst_n.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    cocotb.start_soon(Clock(dut.clk, 1, unit="us").start())
    await ClockCycles(dut.clk, 3)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    await assert_result(dut, 0)

    await command(dut, LOAD_X, 3)
    await command(dut, LOAD_W, 2)
    await command(dut, MAC)
    await assert_result(dut, 6)

    # STB held high must not cause multiple accumulations.
    await FallingEdge(dut.clk)
    dut.ui_in.value = (MAC << 6) | 0x20
    await ClockCycles(dut.clk, 8)
    await assert_result(dut, 12)  # exactly one additional MAC
    await FallingEdge(dut.clk)
    dut.ui_in.value = (MAC << 6)
    await ClockCycles(dut.clk, 2)
    await assert_result(dut, 12)

    # Signed int4: 0b1000 is -8, and 0b0111 is +7.
    await command(dut, LOAD_X, 0x8)
    await command(dut, LOAD_W, 7)
    await command(dut, MAC)     # 12 - 56 = -44: ReLU -> 0
    await assert_result(dut, 0)
    await command(dut, CLEAR)
    await assert_result(dut, 0)

    # Positive saturation: 49 + 49 + 49 clamps at +127.
    await command(dut, LOAD_X, 7)
    await command(dut, LOAD_W, 7)
    for expected in (49, 98, 127, 127):
        await command(dut, MAC)
        await assert_result(dut, expected)

    # Negative saturation (-56 * 3) and subsequent recovery.
    await command(dut, CLEAR)
    await command(dut, LOAD_X, 8)
    await command(dut, LOAD_W, 7)
    for _ in range(4):
        await command(dut, MAC)
        await assert_result(dut, 0)
    await command(dut, LOAD_X, 7)
    await command(dut, MAC)    # -128 + 49 = -79
    await assert_result(dut, 0)
    await command(dut, MAC)    # -79 + 49 = -30
    await assert_result(dut, 0)
    await command(dut, MAC)    # -30 + 49 = 19
    await assert_result(dut, 19)

    # ena disables command execution.
    dut.ena.value = 0
    await command(dut, CLEAR)
    await assert_result(dut, 19)
    dut.ena.value = 1
    await command(dut, CLEAR)
    await assert_result(dut, 0)

    # Asynchronous reset.
    await command(dut, LOAD_X, 4)
    await command(dut, LOAD_W, 5)
    await command(dut, MAC)
    await assert_result(dut, 20)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 0
    await Timer(1, unit="ns")
    await assert_result(dut, 0)
