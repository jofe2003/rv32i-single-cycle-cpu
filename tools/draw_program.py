#!/usr/bin/env python3
"""Desenha o programa da Memória de Instruções como SVG.

Lê rtl/memory/instruction_memory.v, desassembla cada instrução, usa os
comentários do código como descrição e desenha uma seta para cada beq a
partir do destino decodificado do próprio binário (destino = PC + imm).
Assim a figura nunca fica diferente do código.

Uso (na raiz do repositório):
    python3 tools/draw_program.py            # gera docs/img/instruction_memory_program.svg
    python3 tools/draw_program.py --full     # mostra também as tentativas 2 a 9
"""

import argparse
import re
import sys
from dataclasses import dataclass
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "rtl/memory/instruction_memory.v"
OUT = ROOT / "docs/img/instruction_memory_program.svg"


# ---------------------------------------------------------------- leitura

@dataclass
class Instr:
    pc: int
    word: str          # 32 bits, MSB primeiro
    comment: str       # comentário logo acima da instrução
    header: str        # comentário de seção (ex.: "Bloco para tentativa 1")


def parse(path):
    instrs, comment, header, block = [], None, None, None
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if block is not None:                      # dentro de /* ... */ de várias linhas
            if s.endswith("*/"):
                block.append(s[:-2])
                header = " ".join(t.strip() for t in block if t.strip())
                block = None
            else:
                block.append(s)
            continue
        m = re.match(r"Memory\[(\d+)\]\s*=\s*32'b([01]{32});", s)
        if m:
            instrs.append(Instr(int(m[1]), m[2], comment or "", header or ""))
            comment = header = None
        elif s.startswith("/*") and s.endswith("*/"):
            text = s[2:-2].strip()
            if comment:                            # dois comentários seguidos: o 1º vira seção
                header = comment
            comment = text
        elif s.startswith("/*"):
            block = [s[2:]]
    return instrs


# ------------------------------------------------------- desassemblador

def field(w, hi, lo):
    return int(w[31 - hi:32 - lo], 2)


def disasm(w):
    """Retorna (texto, destino_relativo ou None). Imediatos como no imm_gen.v."""
    op = field(w, 6, 0)
    rd, f3 = field(w, 11, 7), field(w, 14, 12)
    rs1, rs2, f7 = field(w, 19, 15), field(w, 24, 20), field(w, 31, 25)
    if op == 0b0110011:
        name = {(0, 0): "add", (32, 0): "sub", (0, 7): "and", (0, 6): "or"}.get((f7, f3), "?")
        return f"{name} x{rd}, x{rs1}, x{rs2}", None
    if op == 0b0000011:
        return f"lw x{rd}, {field(w, 31, 20)}(x{rs1})", None
    if op == 0b0100011:
        imm = (field(w, 31, 25) << 5) | field(w, 11, 7)
        return f"sw x{rs2}, {imm}(x{rs1})", None
    if op == 0b1100011:
        imm = int(w[0] + w[24] + w[1:7] + w[20:24], 2)  # {31, 7, 30:25, 11:8}
        return f"beq x{rs1}, x{rs2}, {imm}", imm
    return f"? {w}", None


# --------------------------------------------------------------- layout

FONT = 15
CHAR = FONT * 0.6          # largura de um caractere monoespaçado
LINE = 25
MARGIN = 28
LANE_GAP = 22

COLORS = {"fail": "#c0392b", "ok": "#1e8449", "end": "#555555"}
LEGEND = {"fail": "acabaram as tentativas → resultado 0",
          "ok": "acertou → resultado 1",
          "end": "fim do programa"}


def classify(asm, target, instrs_by_pc):
    """Tipo da seta, pela instrução no destino."""
    dest = instrs_by_pc.get(target)
    if dest and dest.word == instrs_by_pc[max(instrs_by_pc)].word and target == max(instrs_by_pc):
        return "end"
    if dest and disasm(dest.word)[0].startswith("sw x0"):
        return "fail"
    if dest and disasm(dest.word)[0].startswith("sw"):
        return "ok"
    return "end"


def build_rows(instrs, full):
    """Lista de linhas: ('title'|'header'|'instr'|'ellipsis'|'gap', dado)."""
    blocks = [i for i, ins in enumerate(instrs) if re.search(r"tentativa \d+", ins.header)]
    hide = set()
    if not full and len(blocks) >= 3:
        hide = set(range(blocks[1], blocks[-1]))
    rows = [("title", "Memória de Instruções — programa do jogo")]
    ellipsis_done = False
    for idx, ins in enumerate(instrs):
        if idx in hide:
            if not ellipsis_done:
                first, last = instrs[blocks[1]].pc, instrs[blocks[-1] - 1].pc
                rows += [("gap", None),
                         ("ellipsis", f"…   tentativas 2 a {len(blocks) - 1} (posições {first}–{last}): mesmo padrão"),
                         ("gap", None)]
                ellipsis_done = True
            continue
        if ins.header:
            if rows[-1][0] != "gap":
                rows.append(("gap", None))
            m = re.search(r"tentativa (\d+)", ins.header)
            rows.append(("header", f"/* tentativa {m[1]} */" if m else f"/* {ins.header} */"))
        rows.append(("instr", ins))
    return rows, hide


def render(instrs, full):
    by_pc = {i.pc: i for i in instrs}
    rows, hide = build_rows(instrs, full)
    hidden_pcs = {instrs[i].pc for i in hide}

    # desvios
    branches = []
    for ins in instrs:
        asm, rel = disasm(ins.word)
        if rel is not None:
            branches.append((ins.pc, ins.pc + rel, classify(asm, ins.pc + rel, by_pc)))
    for pc, tgt, _ in branches:
        if tgt not in by_pc:
            print(f"aviso: beq na posição {pc} salta para {tgt}, fora do programa", file=sys.stderr)

    # posição vertical de cada instrução visível
    y, row_y, pc_y = MARGIN + FONT, [], {}
    for kind, data in rows:
        row_y.append(y)
        if kind == "instr":
            pc_y[data.pc] = y
        y += LINE // 2 if kind == "gap" else LINE + (10 if kind == "title" else 0)
    height = y + LINE * (len(LEGEND) + 1) + MARGIN

    # trilhas: uma por destino, a mais longa por fora
    groups = {}
    for pc, tgt, kind in branches:
        if pc in pc_y and tgt in pc_y and pc != tgt:
            groups.setdefault(tgt, []).append(pc)
    def span(t):
        ys = [pc_y[t]] + [pc_y[p] for p in groups[t]]
        return max(ys) - min(ys)
    order = sorted(groups, key=span)
    x_text = MARGIN + LANE_GAP * (len(order) + 1)
    lane_x = {t: x_text - 14 - LANE_GAP * (i + 1) for i, t in enumerate(order)}

    # colunas de texto
    col_asm = x_text + CHAR * 4
    col_cmt = col_asm + CHAR * 29
    longest = max(len(d.comment) for k, d in rows if k == "instr")
    width = int(col_cmt + CHAR * (longest + 2) + MARGIN)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}" font-family="DejaVu Sans Mono, Menlo, Consolas, monospace" '
           f'font-size="{FONT}">',
           '<defs>']
    for k, c in COLORS.items():
        out.append(f'<marker id="a-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
                   f'markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>')
    out += ['</defs>', f'<rect width="{width}" height="{height}" fill="#ffffff"/>']

    # textos
    for (kind, data), ry in zip(rows, row_y):
        if kind == "title":
            out.append(f'<text x="{width / 2}" y="{ry}" text-anchor="middle" font-size="{FONT + 4}" '
                       f'font-weight="bold" fill="#111">{escape(data)}</text>')
        elif kind == "header":
            out.append(f'<text x="{col_asm}" y="{ry}" fill="#777" font-style="italic">{escape(data)}</text>')
        elif kind == "ellipsis":
            out.append(f'<text x="{col_asm}" y="{ry}" fill="#777">{escape(data)}</text>')
        elif kind == "instr":
            asm, rel = disasm(data.word)
            out.append(f'<text x="{x_text}" y="{ry}" fill="#999">{data.pc:>2}</text>')
            out.append(f'<text x="{col_asm}" y="{ry}" fill="#111" font-weight="bold">{escape(asm)}</text>')
            if rel is not None:
                tag = f"→ {data.pc + rel}" + ("  (laço)" if rel == 0 else "")
                out.append(f'<text x="{col_asm + CHAR * (len(asm) + 2)}" y="{ry}" '
                           f'fill="{COLORS[classify(asm, data.pc + rel, by_pc)]}">{tag}</text>')
            out.append(f'<text x="{col_cmt}" y="{ry}" fill="#444">{escape(data.comment)}</text>')

    # setas (centro vertical da linha de texto)
    mid = lambda pc: pc_y[pc] - FONT * 0.35
    x_end = x_text - 6
    for tgt in order:
        kind = next(k for p, t, k in branches if t == tgt)
        c, lx = COLORS[kind], lane_x[tgt]
        ys = [mid(tgt)] + [mid(p) for p in groups[tgt]]
        out.append(f'<line x1="{lx}" y1="{min(ys)}" x2="{lx}" y2="{max(ys)}" stroke="{c}" stroke-width="2"/>')
    for tgt in order:                               # depois das trilhas: ganchos com "ponte" branca
        kind = next(k for p, t, k in branches if t == tgt)
        c, lx = COLORS[kind], lane_x[tgt]
        for p in groups[tgt]:
            yy = mid(p)
            out.append(f'<line x1="{lx}" y1="{yy}" x2="{x_end - 10}" y2="{yy}" stroke="#fff" stroke-width="7"/>')
            out.append(f'<line x1="{lx}" y1="{yy}" x2="{x_end - 10}" y2="{yy}" stroke="{c}" stroke-width="2"/>')
        yy = mid(tgt)
        out.append(f'<line x1="{lx}" y1="{yy}" x2="{x_end}" y2="{yy}" stroke="#fff" stroke-width="7"/>')
        out.append(f'<line x1="{lx}" y1="{yy}" x2="{x_end}" y2="{yy}" stroke="{c}" stroke-width="2" '
                   f'marker-end="url(#a-{kind})"/>')
    # legenda
    ly = row_y[-1] + LINE * 1.6
    for k, text in LEGEND.items():
        out.append(f'<line x1="{x_text}" y1="{ly - 5}" x2="{x_text + 30}" y2="{ly - 5}" stroke="{COLORS[k]}" '
                   f'stroke-width="2" marker-end="url(#a-{k})"/>')
        out.append(f'<text x="{x_text + 42}" y="{ly}" fill="#444">{escape(text)}</text>')
        ly += LINE
    out.append(f'<text x="{width - MARGIN}" y="{ly - LINE}" text-anchor="end" fill="#999" font-size="{FONT - 3}">'
               f'gerado por tools/draw_program.py · destino do beq = PC + imm</text>')
    out.append("</svg>")

    # conferência dos desvios ocultos: mesmo destino que os visíveis do mesmo tipo
    shown = {(disasm(by_pc[p].word)[0].split(",")[:2].__str__(), k): t
             for p, t, k in branches if p not in hidden_pcs}
    for p, t, k in branches:
        if p in hidden_pcs:
            key = (disasm(by_pc[p].word)[0].split(",")[:2].__str__(), k)
            if shown.get(key) not in (None, t):
                print(f"aviso: beq oculto na posição {p} vai para {t}, diferente dos visíveis", file=sys.stderr)
    return "\n".join(out) + "\n", branches


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--full", action="store_true", help="mostra todas as tentativas")
    ap.add_argument("-o", "--output", type=Path, default=OUT)
    args = ap.parse_args()
    svg, branches = render(parse(SRC), args.full)
    args.output.write_text(svg, encoding="utf-8")
    print(f"{args.output.relative_to(ROOT) if args.output.is_absolute() else args.output}: "
          f"{len(branches)} desvios")
    for pc, tgt, kind in branches:
        print(f"  {pc:2d} → {tgt:2d}  ({kind})")


if __name__ == "__main__":
    main()
