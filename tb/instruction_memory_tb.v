`timescale 1ns/100ps

/*
    Testa a Memoria de Instrucoes com o programa do jogo
    (rtl/memory/instruction_memory.v): confere a primeira e a ultima
    instrucoes do programa (posicoes 0 a 47) e verifica que as
    posicoes restantes (48 a 63) valem zero.
*/
module testbench ();
    reg [31:0] PC;
    wire [31:0] instruction;

    InstructionMemory UUT (.PC(PC), .instruction(instruction));

    integer j, errors = 0;
    task Check ;
        input [31:0] expect;
        if (instruction !== expect) begin
                $display ("Error : PC: %d expect: %b got: %b", PC, expect, instruction);
                errors = errors + 1;
        end
    endtask

    initial begin
        /* lw x5, 12(x0): carrega a constante 1 */
        PC = 32'd0;
        #10 Check(32'b00000000110000000010001010000011);

        /* lw x1, 0(x0): carrega a senha */
        PC = 32'd1;
        #10 Check(32'b00000000000000000010000010000011);

        /* lw x2, 1(x0): carrega a quantidade de tentativas */
        PC = 32'd2;
        #10 Check(32'b00000000000100000010000100000011);

        /* sub x2, x2, x5: gasta uma tentativa */
        PC = 32'd6;
        #10 Check(32'b01000000010100010000000100110011);

        /* sw x0, 13(x0): grava resultado 0 (errou) */
        PC = 32'd43;
        #10 Check(32'b00000000000000000010011010100011);

        /* sw x5, 13(x0): grava resultado 1 (acertou) */
        PC = 32'd45;
        #10 Check(32'b00000000010100000010011010100011);

        /* beq x0, x0, 0: trava o PC no fim do programa */
        PC = 32'd47;
        #10 Check(32'b00000000000000000000000001100011);

        /* o restante da memoria e zero */
        for (j = 48; j < 64; j = j + 1) begin
            PC = j;
            #10 Check(32'b0);
        end

        $display("Test finished. Erros: %d", errors);
        $finish;
    end
endmodule
