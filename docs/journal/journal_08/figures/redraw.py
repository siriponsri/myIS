"""Journal figures for World Patent Information, academic formal style.

Design rules, from Elsevier artwork instructions and Tufte / PLOS "Ten Simple
Rules for Better Figures":
  - no title or explanatory text inside the figure; the caption carries it
  - no background fills, boxes, drop shadows or decorative rules
  - panel labels are plain (a), (b), (c)
  - Helvetica only, 8.5-9.5 units, which lands near 7-8 pt at journal width
  - two inks plus grey, readable when printed greyscale
Canvas is 460 units. At the single-column manuscript width (359 pt) that is
0.78 scale; at a 140 mm journal column it is 0.86; at 190 mm it is 1.17.
"""
INK, BLUE, ORANGE, GREY, LGREY, PAPER = "#1A1A1A", "#2166AC", "#D6733A", "#8C8C8C", "#CFCFCF", "#FFFFFF"
FN = 'font-family="Helvetica, Arial, sans-serif"'
W = 460
S_AX, S_LB, S_SM, S_PN = 9.0, 9.5, 8.2, 10.5


def t(x, y, s, size=S_LB, a="start", fill=INK, w=None):
    b = f' font-weight="{w}"' if w else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{a}" fill="{fill}"{b}>{s}</text>'


def panel(x, y, letter):
    return t(x, y, f"({letter})", S_PN, fill=INK, w="bold")


def line(x1, y1, x2, y2, col=INK, w=0.9, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{w}"{d}/>'


def svg(h, b):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" {FN}>\n' + "\n".join(b) + "\n</svg>"


# ---------------------------------------------------------------- Fig 1
def evidence_map():
    h, b = 170, []
    bw, bh = 96, 54
    xs = [8, 118, 250, 360]
    y = 40
    cells = [("Construct", "representations", "five text views"),
             ("Test", "transfer", "no stable winner"),
             ("Freeze", "and confirm", "872 held-out"),
             ("Diagnose", "exposure", "Top-200 pool")]
    for i, (x, (l1, l2, l3)) in enumerate(zip(xs, cells)):
        b.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" fill="none" stroke="{INK}" stroke-width="0.9"/>')
        b.append(t(x + bw / 2, y + 19, l1, S_LB, "middle"))
        b.append(t(x + bw / 2, y + 31, l2, S_LB, "middle"))
        b.append(t(x + bw / 2, y + 46, l3, S_SM, "middle", GREY))
        b.append(t(x + 5, y - 5, f"{i+1}", S_SM, fill=GREY))
    for x in (104, 346):
        b.append(line(x, y + bh / 2, x + 7, y + bh / 2, INK, 0.9))
        b.append(f'<polygon points="{x+7},{y+bh/2-3} {x+13},{y+bh/2} {x+7},{y+bh/2+3}" fill="{INK}"/>')
    xd = 232
    b.append(line(xd, 18, xd, 130, INK, 0.9, "4,3"))
    b.append(t(xd - 6, 14, "development closed", S_SM, "end", INK))
    b.append(line(xd, y + bh / 2, xd + 11, y + bh / 2, INK, 0.9))
    b.append(f'<polygon points="{xd+11},{y+bh/2-3} {xd+17},{y+bh/2} {xd+11},{y+bh/2+3}" fill="{INK}"/>')
    b.append(t(8, 148, "development evidence", S_SM, fill=GREY))
    b.append(t(250, 148, "confirmation and post-confirmatory diagnosis", S_SM, fill=GREY))
    return svg(h, b)


# ---------------------------------------------------------------- Fig 2
def transfer():
    h, b = 262, []
    b.append(panel(8, 16, "a"))
    x0, x1, ay = 40, 440, 58
    lo, hi = 0.330, 0.426
    sx = lambda v: x0 + (x1 - x0) * (v - lo) / (hi - lo)
    groups = [("Arctic", [0.337430, 0.341341, 0.338268]),
              ("Qwen3", [0.362570, 0.359497, 0.360615]),
              ("PatEmbed", [0.418436, 0.418715, 0.419274])]
    b.append(line(x0, ay + 26, x1, ay + 26, INK, 0.9))
    for v in [0.34, 0.36, 0.38, 0.40, 0.42]:
        b.append(line(sx(v), ay + 26, sx(v), ay + 30, INK, 0.9))
        b.append(t(sx(v), ay + 41, f"{v:.2f}", S_AX, "middle"))
    b.append(t((x0 + x1) / 2, ay + 55, "Development Recall@100", S_LB, "middle"))
    for name, vs in groups:
        for v in vs:
            b.append(f'<circle cx="{sx(v):.1f}" cy="{ay}" r="3.2" fill="none" stroke="{BLUE}" stroke-width="1.3"/>')
        b.append(t(sx(sum(vs) / 3), ay - 14, name, S_AX, "middle"))
    gy = ay + 12
    b.append(line(sx(0.341341), gy, sx(0.359497), gy, INK, 0.8))
    for e in (0.341341, 0.359497):
        b.append(line(sx(e), gy - 3, sx(e), gy + 3, INK, 0.8))
    b.append(t((sx(0.341341) + sx(0.359497)) / 2, gy + 10, "0.018", S_SM, "middle"))

    b.append(panel(8, 132, "b"))
    lab, cw = 74, 118
    xo = lambda j: 40 + lab + j * cw
    top = 146
    cols = ["PatEmbed", "Arctic", "Qwen3"]
    rows = ["PatEmbed", "Arctic", "Qwen3"]
    vals = [["0.418436", "0.337430", "0.362570"], ["0.418715", "0.341341", "0.359497"],
            ["0.419274", "0.338268", "0.360615"]]
    rng = ["0.000838", "0.003911", "0.003073"]
    best = {0: 2, 1: 1, 2: 0}
    b.append(t(40, top, "source", S_AX, fill=GREY))
    b.append(t(40 + lab + 1.5 * cw, top - 14, "consuming retriever", S_AX, "middle", GREY))
    for j, c in enumerate(cols):
        b.append(t(xo(j) + cw / 2, top, c, S_LB, "middle"))
    b.append(line(40, top + 6, 40 + lab + 3 * cw, top + 6, INK, 0.9))
    for i in range(3):
        y = top + 26 + i * 20
        b.append(t(40, y, rows[i], S_LB))
        for j in range(3):
            hit = best[j] == i
            b.append(t(xo(j) + cw / 2, y, vals[i][j], S_LB, "middle", INK, "bold" if hit else None))
            if i == j:
                b.append(f'<circle cx="{xo(j)+cw/2-40:.1f}" cy="{y-3.2}" r="2.6" fill="{INK}"/>')
    yr = top + 26 + 3 * 20
    b.append(line(40, yr - 13, 40 + lab + 3 * cw, yr - 13, LGREY, 0.8))
    b.append(t(40, yr, "range", S_AX, fill=GREY))
    for j in range(3):
        b.append(t(xo(j) + cw / 2, yr, rng[j], S_AX, "middle", GREY))
    b.append(line(40, yr + 7, 40 + lab + 3 * cw, yr + 7, INK, 0.9))
    b.append(t(40, yr + 24, "Bold: highest value in the column.  Filled dot: source and target are the same system.",
               S_SM, fill=GREY))
    return svg(h, b)


# ---------------------------------------------------------------- Fig 3
def confirmation():
    h, b = 300, []
    b.append(panel(8, 16, "a"))
    ax0, ax1 = 100, 300
    sx = lambda v: ax0 + (ax1 - ax0) * (v - 0.25) / (0.45 - 0.25)
    for i, (nm, c, s_) in enumerate([("Recall@100", 0.331, 0.442), ("nDCG@100", 0.279, 0.366)]):
        y = 40 + i * 30
        b.append(t(ax0 - 8, y + 3, nm, S_LB, "end"))
        b.append(line(sx(c), y, sx(s_), y, LGREY, 1.2))
        b.append(f'<circle cx="{sx(c):.1f}" cy="{y}" r="3.4" fill="none" stroke="{INK}" stroke-width="1.2"/>')
        b.append(f'<circle cx="{sx(s_):.1f}" cy="{y}" r="3.4" fill="{BLUE}"/>')
        b.append(t(sx(c), y - 8, f"{c:.3f}", S_SM, "middle", GREY))
        b.append(t(sx(s_), y - 8, f"{s_:.3f}", S_SM, "middle", BLUE))
    ay = 40 + 30 + 18
    b.append(line(ax0, ay, ax1, ay, INK, 0.9))
    for v in [0.25, 0.30, 0.35, 0.40, 0.45]:
        b.append(line(sx(v), ay, sx(v), ay + 4, INK, 0.9))
        b.append(t(sx(v), ay + 15, f"{v:.2f}", S_AX, "middle"))
    b.append(t((ax0 + ax1) / 2, ay + 29, "Metric value", S_LB, "middle"))
    b.append(f'<circle cx="336" cy="37" r="3.4" fill="none" stroke="{INK}" stroke-width="1.2"/>')
    b.append(t(344, 40, "comparator", S_AX))
    b.append(f'<circle cx="336" cy="52" r="3.4" fill="{BLUE}"/>')
    b.append(t(344, 55, "selected", S_AX))

    b.append(panel(8, 148, "b"))
    bx0, bx1 = 100, 300
    px = lambda v: bx0 + (bx1 - bx0) * v / 0.13
    for i, (nm, d, lo, hi) in enumerate([("Recall@100", 0.111, 0.102, 0.120), ("nDCG@100", 0.086, 0.079, 0.094)]):
        y = 168 + i * 26
        b.append(t(bx0 - 8, y + 3, nm, S_LB, "end"))
        b.append(line(px(lo), y, px(hi), y, INK, 1.1))
        for e in (lo, hi):
            b.append(line(px(e), y - 3.5, px(e), y + 3.5, INK, 1.1))
        b.append(f'<circle cx="{px(d):.1f}" cy="{y}" r="3.4" fill="{ORANGE}"/>')
        b.append(t(px(hi) + 8, y + 3, f"{d:+.3f} [{lo:.3f}, {hi:.3f}]", S_SM, fill=INK))
    by = 168 + 26 + 18
    b.append(line(px(0), 160, px(0), by, GREY, 0.8, "3,2"))
    b.append(line(bx0, by, bx1, by, INK, 0.9))
    for v in [0, 0.04, 0.08, 0.12]:
        b.append(line(px(v), by, px(v), by + 4, INK, 0.9))
        b.append(t(px(v), by + 15, f"{v:.2f}", S_AX, "middle"))
    b.append(t((bx0 + bx1) / 2, by + 29, "Paired difference, 95% bootstrap CI", S_LB, "middle"))

    b.append(panel(8, 272, "c"))
    x, bw, ybar = 40, 400, 264
    for frac, fill, stroke, lab in [(619 / 872, BLUE, BLUE, "wins 619 (71.0%)"),
                                    (158 / 872, PAPER, GREY, "ties 158 (18.1%)"),
                                    (95 / 872, ORANGE, ORANGE, "losses 95 (10.9%)")]:
        wd = bw * frac
        b.append(f'<rect x="{x:.1f}" y="{ybar}" width="{wd:.1f}" height="11" fill="{fill}" stroke="{stroke}" stroke-width="0.8"/>')
        x += wd
    lx = 40
    for fill, stroke, lab in [(BLUE, BLUE, "wins 619 (71.0%)"), (PAPER, GREY, "ties 158 (18.1%)"),
                              (ORANGE, ORANGE, "losses 95 (10.9%)")]:
        b.append(f'<rect x="{lx}" y="{ybar+19}" width="8" height="8" fill="{fill}" stroke="{stroke}" stroke-width="0.8"/>')
        b.append(t(lx + 13, ybar + 26, lab, S_AX))
        lx += 140
    return svg(h, b)


# ---------------------------------------------------------------- Fig 4
def diagnosis():
    h, b = 212, []
    b.append(panel(8, 16, "a"))
    x, bw, by = 40, 400, 30
    segs = [(796 / 5193, BLUE, BLUE, "796 found by rank 100"),
            (332 / 5193, PAPER, GREY, "332 first found at ranks 101-200"),
            (4065 / 5193, ORANGE, ORANGE, "4,065 absent from Top-200")]
    for frac, fill, stroke, _ in segs:
        wd = bw * frac
        b.append(f'<rect x="{x:.1f}" y="{by}" width="{wd:.1f}" height="13" fill="{fill}" stroke="{stroke}" stroke-width="0.8"/>')
        x += wd
    b.append(t(40, by - 6, "relevant-family incidences, n = 5,193", S_AX, fill=GREY))
    ly = by + 26
    for i, (frac, fill, stroke, lab) in enumerate(segs):
        yy = ly + i * 13
        b.append(f'<rect x="40" y="{yy-7}" width="8" height="8" fill="{fill}" stroke="{stroke}" stroke-width="0.8"/>')
        b.append(t(53, yy, f"{lab}  ({frac*100:.1f}%)", S_AX))

    b.append(panel(8, 122, "b"))
    x0, x1 = 100, 380
    sx = lambda v: x0 + (x1 - x0) * (v - 0.18) / (0.27 - 0.18)
    y = 142
    b.append(line(sx(0.188), y, sx(0.260), y, LGREY, 1.2))
    b.append(f'<circle cx="{sx(0.188):.1f}" cy="{y}" r="3.4" fill="none" stroke="{INK}" stroke-width="1.2"/>')
    b.append(f'<circle cx="{sx(0.260):.1f}" cy="{y}" r="3.4" fill="{ORANGE}"/>')
    b.append(t(sx(0.188), y - 8, "0.188 observed", S_SM, "middle"))
    b.append(t(sx(0.260), y - 8, "0.260 bound", S_SM, "middle"))
    b.append(t((sx(0.188) + sx(0.260)) / 2, y + 14, "+0.072", S_SM, "middle"))
    ay = y + 26
    b.append(line(x0, ay, x1, ay, INK, 0.9))
    for v in [0.18, 0.21, 0.24, 0.27]:
        b.append(line(sx(v), ay, sx(v), ay + 4, INK, 0.9))
        b.append(t(sx(v), ay + 15, f"{v:.2f}", S_AX, "middle"))
    b.append(t((x0 + x1) / 2, ay + 29, "Macro Recall@100, 905 judged queries", S_LB, "middle"))
    return svg(h, b)


# ---------------------------------------------------------------- Fig 5
def depth():
    h, b = 194, []
    depths = [200, 300, 500, 1000]
    bound = [0.260, 0.318, 0.410, 0.529]
    absent = [78.3, 73.7, 66.5, 56.9]
    x0, x1, y0, y1 = 46, 214, 150, 34
    ax = lambda i: x0 + (x1 - x0) * i / 3
    ay = lambda v: y1 + (y0 - y1) * (0.56 - v) / (0.56 - 0.16)
    b.append(panel(8, 16, "a"))
    b.append(line(x0, y0, x1, y0, INK, 0.9))
    b.append(line(x0, y0, x0, y1, INK, 0.9))
    for v in [0.2, 0.3, 0.4, 0.5]:
        b.append(line(x0 - 4, ay(v), x0, ay(v), INK, 0.9))
        b.append(t(x0 - 7, ay(v) + 3, f"{v:.1f}", S_AX, "end"))
    b.append(line(x0, ay(0.188), x1, ay(0.188), GREY, 0.8, "3,2"))
    b.append(t(x1, ay(0.188) - 5, "observed 0.188", S_SM, "end", GREY))
    b.append(f'<polyline points="{" ".join(f"{ax(i):.1f},{ay(v):.1f}" for i,v in enumerate(bound))}" fill="none" stroke="{BLUE}" stroke-width="1.3"/>')
    for i, (d, v) in enumerate(zip(depths, bound)):
        b.append(f'<circle cx="{ax(i):.1f}" cy="{ay(v):.1f}" r="3" fill="{BLUE}"/>')
        b.append(t(ax(i) + (12 if i == 0 else 0), ay(v) - 8, f"{v:.3f}", S_SM, "start" if i == 0 else "middle", BLUE))
        b.append(line(ax(i), y0, ax(i), y0 + 4, INK, 0.9))
        b.append(t(ax(i), y0 + 15, str(d), S_AX, "middle"))
    b.append(t((x0 + x1) / 2, y0 + 29, "Pool depth", S_LB, "middle"))
    b.append('<text x="%.1f" y="%.1f" font-size="%s" text-anchor="middle" fill="%s" transform="rotate(-90 %.1f %.1f)">Recall@100</text>' % (x0-32, (y0+y1)/2, S_LB, INK, x0-32, (y0+y1)/2))

    px0, px1 = 292, 440
    bx = lambda i: px0 + (px1 - px0) * i / 3
    byy = lambda v: y1 + (y0 - y1) * (82 - v) / (82 - 52)
    b.append(panel(254, 16, "b"))
    b.append(line(px0, y0, px1, y0, INK, 0.9))
    b.append(line(px0, y0, px0, y1, INK, 0.9))
    for v in [60, 70, 80]:
        b.append(line(px0 - 4, byy(v), px0, byy(v), INK, 0.9))
        b.append(t(px0 - 7, byy(v) + 3, str(v), S_AX, "end"))
    b.append(f'<polyline points="{" ".join(f"{bx(i):.1f},{byy(v):.1f}" for i,v in enumerate(absent))}" fill="none" stroke="{ORANGE}" stroke-width="1.3"/>')
    for i, (d, v) in enumerate(zip(depths, absent)):
        b.append(f'<circle cx="{bx(i):.1f}" cy="{byy(v):.1f}" r="3" fill="{ORANGE}"/>')
        b.append(t(bx(i) + (10 if i == 0 else 0), byy(v) - 8, f"{v:.1f}", S_SM, "start" if i == 0 else "middle", ORANGE))
        b.append(line(bx(i), y0, bx(i), y0 + 4, INK, 0.9))
        b.append(t(bx(i), y0 + 15, str(d), S_AX, "middle"))
    b.append(t((px0 + px1) / 2, y0 + 29, "Pool depth", S_LB, "middle"))
    b.append('<text x="%.1f" y="%.1f" font-size="%s" text-anchor="middle" fill="%s" transform="rotate(-90 %.1f %.1f)">Absent (%%)</text>' % (px0-30, (y0+y1)/2, S_LB, INK, px0-30, (y0+y1)/2))
    return svg(h, b)


# ---------------------------------------------------------------- Fig 6
def sections():
    sec = [("A  Human necessities", 102, 76.2), ("B  Operations, transport", 290, 81.8),
           ("C  Chemistry, metallurgy", 127, 72.6), ("D  Textiles, paper", 60, 71.2),
           ("E  Fixed constructions", 63, 77.0), ("F  Mechanical engineering", 133, 80.2),
           ("G  Physics", 98, 74.7), ("H  Electricity", 31, 92.5)]
    h, b = 218, []
    lx, rx = 190, 428
    vx = lambda v: lx + (rx - lx) * v / 100
    y = 26
    for name, n, rate in sec:
        b.append(t(8, y + 3, name, S_LB))
        b.append(t(184, y + 3, f"n={n}", S_AX, "end", GREY))
        b.append(line(lx, y, rx, y, LGREY, 0.6, "1,2"))
        b.append(f'<circle cx="{vx(rate):.1f}" cy="{y}" r="3.4" fill="{ORANGE}"/>')
        b.append(t(vx(rate) + 8, y + 3, f"{rate:.1f}", S_SM, fill=INK))
        y += 20
    ay = y + 2
    b.append(line(lx, ay, rx, ay, INK, 0.9))
    for v in [0, 25, 50, 75, 100]:
        b.append(line(vx(v), ay, vx(v), ay + 4, INK, 0.9))
        b.append(t(vx(v), ay + 15, str(v), S_AX, "middle"))
    b.append(t((lx + rx) / 2, ay + 29, "Relevant families absent from the Top-200 pool (%)", S_LB, "middle"))
    return svg(h, b)


if __name__ == "__main__":
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF
    for n, f in [("overview_evidence_map", evidence_map), ("fig1_a3_transfer", transfer),
                 ("fig2_a5_confirmation", confirmation), ("fig3_a7_diagnosis", diagnosis),
                 ("fig5_depth_vs_ordering", depth), ("fig6_section_exposure", sections)]:
        open(n + ".svg", "w").write(f())
        renderPDF.drawToFile(svg2rlg(n + ".svg"), n + ".pdf")
        print("built", n)
