<p align="center">
  <img src="./GrupoCessar.png" width="100%"/>
</p>

# Processador RISC-V monociclo em Verilog

## Descrição

Implementação de um processador **RISC-V monociclo (subconjunto RV32I)** em Verilog, feita como projeto da disciplina **PCS3115 – Sistemas Digitais I** da Escola Politécnica da USP (2022) pelo Grupo 3 (Grupo Cessar):

- [Celso Tadaki Sinoka](https://github.com/C-Tadaki-S)
- [Henrique Gregory Gimenez](https://github.com/henriquegreg)
- [João Felipe de Souza Melo](https://github.com/jofe2003)
- [Lucas Suzin Bertan](https://github.com/bertanbee)

O processador roda um programa já carregado na Memória de Instruções: o **jogo de adivinhação** ("Numle") do EP0 da disciplina MAC2166 – Introdução à Computação. A senha e as tentativas do jogador ficam na Memória de Dados, e o resultado (1 = acertou, 0 = errou) é escrito de volta nela.

Cada bloco do datapath (ALU, controle, registradores, memórias, gerador de imediatos, mux, somadores) é um módulo separado, com testbench própria, comentários no código e um README que explica o seu funcionamento.

O código C original do jogo, a tradução instrução por instrução para RISC-V e as formas de onda da simulação estão em [`InstructionMemory/README.md`](InstructionMemory/README.md).

![Diagrama do circuito](Circuito.jpg)

Circuito sintetizado:

![Circuito sintetizado](sintetizado.jpeg)

Também foi feita uma implementação para FPGA (Intel Cyclone V):

![Pin planner da FPGA](riscv-fpga-pinplanner.png)

### Instruções suportadas

| Instrução | Tipo | Descrição |
|---|---|---|
| `add` | R | `rd = rs1 + rs2` |
| `sub` | R | `rd = rs1 - rs2` |
| `and` | R | `rd = rs1 & rs2` (bit a bit) |
| `or`  | R | `rd = rs1 \| rs2` (bit a bit) |
| `lw`  | I | `rd = Mem[rs1 + imm]` |
| `sw`  | S | `Mem[rs1 + imm] = rs2` |
| `beq` | B | se `rs1 == rs2` (subtração dá zero), `PC = PC + imm` |

![Formato das instruções](instructionset.png)

| Campo | Significado |
|---|---|
| `rs1`, `rs2` | registradores de origem |
| `rd` | registrador de destino |
| `imm` | valor imediato embutido na instrução |
| `opcode` | identifica o tipo de instrução (R, I, S, B…) |
| `funct3`, `funct7` | diferenciam instruções com o mesmo opcode (ex.: `add` × `sub`) |

> **Observação:** as memórias são endereçadas por palavra, ou seja, o PC avança de 1 em 1 (e não de 4 em 4 como no RISC-V padrão). A Memória de Dados tem 32 palavras de 32 bits e a de Instruções, 64.

## Requisitos

- [Icarus Verilog](https://steveicarus.github.io/iverilog/) (`iverilog` e `vvp`) — compilação e simulação
- [GTKWave](https://gtkwave.sourceforge.net/) — visualização das formas de onda
- Opcional: [Questa – Intel FPGA Edition](https://www.intel.com/content/www/us/en/software/programmable/quartus-prime/questa-edition.html) — foi usado nas testbenches individuais
- Opcional: Intel Quartus Prime — síntese para FPGA Cyclone V
- Opcional: `gcc` — para compilar o gerador da Memória de Dados

## Instalação

Não há etapa de build: basta clonar o repositório e instalar as ferramentas.

```bash
git clone https://github.com/jofe2003/-rv32i-single-cycle-cpu.git
cd -- -rv32i-single-cycle-cpu
```

Ubuntu/Debian:

```bash
sudo apt install iverilog gtkwave
```

macOS (Homebrew):

```bash
brew install icarus-verilog
brew install --cask gtkwave
```

## Uso

### Simular o processador completo

Na **raiz do repositório** (os `` `include `` usam caminhos relativos a ela):

```bash
iverilog -Wall -I ./ALU -I ./ALU/operations -I ./adders -o riscv.vvp risc-v.v risc-v_TB.v
vvp riscv.vvp
gtkwave my_dumpfile.vcd
```

A simulação gera `my_dumpfile.vcd` com todos os sinais do módulo `riscv`. No GTKWave, o resultado do jogo pode ser visto na Memória de Dados:

![GTKWave](gtkwave.png)

Se der erro de arquivo não encontrado nos `` `include ``, confira se o comando foi executado na raiz e se as flags `-I` estão presentes ([discussão no Stack Overflow](https://stackoverflow.com/questions/47449489/how-to-include-files-in-icarus-verilog)).

### Testar um módulo isolado

Cada pasta tem o módulo e sua testbench. Com Icarus Verilog, por exemplo:

```bash
cd mux
iverilog -o tb.vvp mux.v mux_TB.v && vvp tb.vvp
```

Para a ALU, que inclui as operações em `operations/`:

```bash
cd ALU
iverilog -I operations -o tb.vvp ALU.v ALU_tb.v && vvp tb.vvp
```

Com Questa:

```bash
vlog modulo.v
vlog modulo_tb.v
vsim -c work.testbench
# dentro do simulador:
run 10000ns
quit
```

O tempo do `run` depende de cada testbench: veja os atrasos (`#...`) no arquivo para escolher um valor suficiente.

### Mudar as entradas do jogo

O programa `DataMemory/generate_datamem.c` gera um novo `DataMemory.v` com a senha e as tentativas que você escolher:

```bash
cd DataMemory
gcc generate_datamem.c -o generator
printf "4\n3\n1\n2\n3\n" | ./generator > DataMemory.v
```

Entradas, uma por linha: a senha (0–9), o número de tentativas *n* (0–9) e as *n* tentativas (0–9 cada). Atenção: isso **sobrescreve** o `DataMemory.v` atual.

## Estrutura de pastas

```
.
├── risc-v.v                 # módulo topo: liga todos os blocos do datapath
├── risc-v_TB.v              # testbench do processador completo (reset + 100 µs)
├── ALU/                     # ALU (add, sub, and, or) + testbench
│   └── operations/          # somador/subtrator carry/borrow look-ahead, and, or
├── ALU_Control/             # controle da ALU (decodifica ALUOp + funct)
├── Control-Monocycle/       # unidade de controle principal (decodifica o opcode)
├── ClockGenerator/          # gerador de clock (período de 100 ns)
├── Registers/               # banco de 32 registradores e Program Counter
├── ImmediateGenerator/      # extrai o imediato dos formatos I, S e B
├── InstructionMemory/       # programa do jogo em binário + capturas da simulação
├── DataMemory/              # memória de dados e o gerador em C
├── mux/                     # multiplexador 2:1 de 32 bits
├── adders/                  # somador de 32 bits (PC + 1, PC + imm)
├── randomGenerator/         # gerador pseudoaleatório (não usado no topo; mantido por completude)
├── Circuito.jpg             # diagrama do datapath
├── sintetizado.jpeg         # circuito sintetizado
├── riscv-fpga-pinplanner.png# mapeamento de pinos na FPGA
├── instructionset.png       # formatos de instrução
└── gtkwave.png              # exemplo de simulação
```

## Hardware

A síntese foi feita para a FPGA **[Intel Cyclone V](https://www.intel.com/content/www/us/en/products/details/fpga/cyclone/v.html)**. No levantamento de custos feito em 2022, os kits de desenvolvimento com Cyclone V custavam a partir de R$ 1.500. Só achamos preço da placa avulsa para a geração anterior, a Cyclone IV, entre R$ 200 e R$ 300. Outra alternativa voltada ao ensino de RISC-V é a placa [Perf-V](https://perfv.org/).

## Referências

- Waterman, A. et al. *The RISC-V Instruction Set Manual, Volume I: User-Level ISA*, v2.2. SiFive, 2017. https://riscv.org/wp-content/uploads/2017/05/riscv-spec-v2.2.pdf
- Patterson, D.; Hennessy, J. *Computer Organization and Design: RISC-V Edition*. 2018.
- Patterson, D.; Waterman, A. *Guia Prático RISC-V: Atlas de uma Arquitetura Aberta*. 2019. http://riscvbook.com/portuguese/guia-pratico-risc-v-1.0.0.pdf
- Azevedo, R. J. Canal no YouTube. https://www.youtube.com/@rjazevedo
- Albertini, B. *Sistemas Digitais*. https://balbertini.github.io/pages/sd-pt_BR.html#sd
