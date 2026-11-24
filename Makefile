# Simulação do processador RISC-V monociclo com Icarus Verilog.
#
#   make sim          compila e simula o processador (gera build/my_dumpfile.vcd)
#   make wave         abre as formas de onda no GTKWave
#   make test         roda todas as testbenches de módulo
#   make test-alu     roda uma testbench específica (ver TESTS abaixo)
#   make clean        apaga build/

IVERILOG ?= iverilog
VVP      ?= vvp
GTKWAVE  ?= gtkwave
IVFLAGS  ?= -Wall -Wno-timescale
BUILD    := build

# Ordem: clock_gen.v vem primeiro porque define o `timescale.
COMMON_SRC := rtl/common/clock_gen.v rtl/common/lookahead_1b.v rtl/common/adder32.v rtl/common/mux2.v
ALU_SRC    := rtl/alu/ops/and.v rtl/alu/ops/or.v rtl/alu/ops/lookahead_1b_alu.v rtl/alu/ops/add.v \
              rtl/alu/ops/borrowahead_1b.v rtl/alu/ops/sub.v rtl/alu/alu.v
CORE_SRC   := rtl/core/pc.v rtl/core/control_unit.v rtl/core/alu_control.v rtl/core/imm_gen.v rtl/core/register_file.v
MEM_SRC    := rtl/memory/instruction_memory.v rtl/memory/data_memory.v
RTL_SRC    := $(COMMON_SRC) $(ALU_SRC) $(CORE_SRC) $(MEM_SRC) rtl/riscv_top.v

# Fontes de cada testbench de módulo
alu_SRC                := $(ALU_SRC) tb/alu_tb.v
alu_control_SRC        := rtl/core/alu_control.v tb/alu_control_tb.v
control_unit_SRC       := rtl/core/control_unit.v tb/control_unit_tb.v
data_memory_SRC        := rtl/memory/data_memory.v tb/data_memory_tb.v
imm_gen_SRC            := rtl/core/imm_gen.v tb/imm_gen_tb.v
instruction_memory_SRC := rtl/memory/instruction_memory.v tb/instruction_memory_tb.v
pc_SRC                 := rtl/core/pc.v tb/pc_tb.v
register_file_SRC      := rtl/core/register_file.v tb/register_file_tb.v
mux2_SRC               := rtl/common/mux2.v tb/mux2_tb.v
random_gen_SRC         := extras/random_gen/random_gen.v extras/random_gen/random_gen_tb.v

TESTS := alu alu_control control_unit data_memory imm_gen instruction_memory pc register_file mux2 random_gen

.PHONY: all sim wave test $(addprefix test-,$(TESTS)) clean

all: sim

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/riscv.vvp: $(RTL_SRC) tb/riscv_top_tb.v | $(BUILD)
	$(IVERILOG) $(IVFLAGS) -o $@ $^

sim: $(BUILD)/riscv.vvp
	cd $(BUILD) && $(VVP) -n riscv.vvp

wave: $(BUILD)/my_dumpfile.vcd
	$(GTKWAVE) $<

$(BUILD)/my_dumpfile.vcd: $(BUILD)/riscv.vvp
	cd $(BUILD) && $(VVP) -n riscv.vvp

# -n: $stop encerra a simulação em vez de abrir o prompt interativo
define TEST_RULE
$(BUILD)/$(1)_tb.vvp: $$($(1)_SRC) | $(BUILD)
	$(IVERILOG) $(IVFLAGS) -o $$@ $$^

test-$(1): $(BUILD)/$(1)_tb.vvp
	@echo "=== $(1)"
	@cd $(BUILD) && $(VVP) -n $(1)_tb.vvp
endef
$(foreach t,$(TESTS),$(eval $(call TEST_RULE,$(t))))

test: $(addprefix test-,$(TESTS))

clean:
	rm -rf $(BUILD)
