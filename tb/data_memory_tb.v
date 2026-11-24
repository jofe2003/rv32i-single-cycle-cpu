`timescale 1ns/100ps

/*
    Testa a Memoria de Dados com o conteudo inicial do jogo
    (rtl/memory/data_memory.v): senha 9, 10 tentativas (0 a 9) e a
    posicao 12 valendo 1. Depois testa escrita sincrona seguida de leitura.
*/
module testbench ();
    reg clk;
    reg mem_read;
    reg mem_write;
    reg [31:0] endereco;
    reg [31:0] write_data;
    wire [31:0] read_data;

    data_memory UUT (.clk(clk), .mem_read(mem_read), .mem_write(mem_write), .endereco(endereco), .write_data(write_data), .read_data(read_data));

    integer i, errors = 0;

    task Check;
        input [31:0] expect;

        if (read_data !== expect) begin
                $display ("Error : endereco: %d expect: %b got: %b", endereco, expect, read_data);
                errors = errors + 1;
        end
    endtask

    initial clk = 0;
    always #10 clk =~ clk;

    initial begin
        // testa a leitura do conteudo inicial
        mem_read = 1'b1;
        mem_write = 1'b0;

        endereco = 32'd0;      // senha
        #5 Check(32'd9);
        endereco = 32'd1;      // quantidade de tentativas
        #5 Check(32'd10);
        for (i = 0; i < 10; i = i + 1) begin
            endereco = 32'd2 + i;  // tentativas 0, 1, ..., 9
            #5 Check(i);
        end
        endereco = 32'd12;     // constante 1 usada pelo programa
        #5 Check(32'd1);

        // testa a escrita: so deve acontecer na borda de subida do clock
        @(negedge clk);
        mem_write = 1'b1;
        endereco = 32'd13;     // posicao do resultado do jogo
        write_data = 32'd111;
        #1 Check(32'bx);       // antes da borda, a posicao ainda nao foi escrita

        // depois da borda, a leitura no mesmo endereco ja ve o novo valor
        @(posedge clk);
        #1 Check(32'd111);

        // com mem_write desligado, a memoria nao muda
        mem_write = 1'b0;
        write_data = 32'd222;
        @(posedge clk);
        #1 Check(32'd111);

        // a escrita em uma posicao nao altera as outras
        endereco = 32'd0;
        #5 Check(32'd9);

        $display("Test finished. Erros: %d", errors);
        $finish;
    end
endmodule
