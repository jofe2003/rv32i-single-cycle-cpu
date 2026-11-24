`timescale 1ns/100ps

/*
    Testa o banco de registradores: valor inicial zero, escrita sincrona,
    leitura assincrona (ja reflete a escrita sem trocar o endereco) e
    o registrador x0, que no RISC-V sempre vale zero.
*/
module testbench () ;
    reg [4:0] readRegister1;
    reg [4:0] readRegister2;
    reg [4:0] writeRegister;
    reg [31:0] writeData;
    reg regWrite;
    reg clk;
    wire [31:0] readData1;
    wire [31:0] readData2;

    Registers UUT (.readRegister1(readRegister1), .readRegister2(readRegister2), .writeRegister(writeRegister),
                   .writeData(writeData), .regWrite(regWrite), .clk(clk), .readData1(readData1), .readData2(readData2));

    integer i, errors = 0;
    task Check ;
        input [31:0] expect1;
        input [31:0] expect2;

        if (readData1 !== expect1 || readData2 !== expect2) begin
                $display ("Error : readRegister1: %d readRegister2: %d expect1: %b got: %b expect2: %b got: %b", readRegister1, readRegister2, expect1, readData1, expect2, readData2);
                errors = errors + 1;
        end
    endtask

    /* escreve 'data' no registrador 'r' na proxima borda de subida */
    task Write;
        input [4:0] r;
        input [31:0] data;
        begin
            @(negedge clk);
            regWrite = 1'b1;
            writeRegister = r;
            writeData = data;
            @(posedge clk);
            #1 regWrite = 1'b0;
        end
    endtask

    initial clk = 1'b0;
    always #10 clk = ~clk;

    initial begin
        regWrite = 1'b0;
        writeRegister = 5'd0;
        writeData = 32'd0;

        /* todos os registradores comecam em zero */
        for (i = 0; i < 32; i = i + 2) begin
            readRegister1 = i;
            readRegister2 = i + 1;
            #1 Check(32'd0, 32'd0);
        end

        /* le x1 e x2 enquanto eles sao escritos: a leitura deve
           atualizar sem precisar trocar o endereco */
        readRegister1 = 5'd1;
        readRegister2 = 5'd2;
        Write(5'd1, 32'd1);
        Check(32'd1, 32'd0);
        Write(5'd2, 32'hDEADBEEF);
        Check(32'd1, 32'hDEADBEEF);

        /* sem regWrite, nada e escrito */
        @(negedge clk);
        writeRegister = 5'd1;
        writeData = 32'd99;
        @(posedge clk);
        #1 Check(32'd1, 32'hDEADBEEF);

        /* x0 ignora escritas e continua valendo zero */
        Write(5'd0, 32'd1);
        readRegister1 = 5'd0;
        #1 Check(32'd0, 32'hDEADBEEF);

        /* ultimo registrador */
        Write(5'd31, 32'd31);
        readRegister1 = 5'd31;
        #1 Check(32'd31, 32'hDEADBEEF);

        $display (" Test ended , %2d errors ", errors );
        $finish;
    end
endmodule
