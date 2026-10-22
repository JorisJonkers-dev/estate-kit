import html

# Dark theme. Later keys in a draw.io style override earlier ones, so every
# vertex starts from BASE_V and every edge from BASE_E.
BG = "#1e1e1e"
INK = "#e8e8e8"
LINE = "#a8a8a8"
F = "fontSize=15;fontFamily=Helvetica;"
BASE_V = f"fillColor=#2b2b2b;strokeColor={LINE};fontColor={INK};"
BASE_E = f"strokeColor={LINE};fontColor={INK};labelBackgroundColor={BG};strokeWidth=1.5;"
ACCENT = "fillColor=#1f3a5f;strokeColor=#7aa7e0;"
DATA = "fillColor=#3a3220;strokeColor=#c9a74a;"
BAD = "fillColor=#4a2525;strokeColor=#d47a7a;"
GOOD = "fillColor=#21402a;strokeColor=#7fc08c;"
WARN = "fillColor=#4a3820;strokeColor=#d9a050;"
BOX = "fillColor=#242424;strokeColor=#5c5c5c;dashed=1;"
ACTOR = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;outlineConnect=0;fillColor=none;"


def esc(s):
    return html.escape(s, quote=True)


class D:
    def __init__(self):
        self.cells = []
        self.n = 0

    def nid(self):
        self.n += 1
        return f"c{self.n}"

    def v(self, label, style, x, y, w, h):
        cid = self.nid()
        self.cells.append(
            f'<mxCell id="{cid}" value="{esc(label)}" style="{BASE_V}{F}html=1;whiteSpace=wrap;{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return cid

    def _pts(self, pts):
        if not pts:
            return ""
        return '<Array as="points">' + "".join(f'<mxPoint x="{a}" y="{b}"/>' for a, b in pts) + "</Array>"

    def e(self, src, tgt, label="", style="", pts=None):
        cid = self.nid()
        self.cells.append(
            f'<mxCell id="{cid}" value="{esc(label)}" style="{BASE_E}{F}html=1;{style}" edge="1" parent="1" source="{src}" target="{tgt}">'
            f'<mxGeometry relative="1" as="geometry">{self._pts(pts)}</mxGeometry></mxCell>')

    def pe(self, x1, y1, x2, y2, label="", style="", pts=None):
        cid = self.nid()
        self.cells.append(
            f'<mxCell id="{cid}" value="{esc(label)}" style="{BASE_E}{F}html=1;{style}" edge="1" parent="1">'
            f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x1}" y="{y1}" as="sourcePoint"/>'
            f'<mxPoint x="{x2}" y="{y2}" as="targetPoint"/>{self._pts(pts)}</mxGeometry></mxCell>')

    def save(self, name):
        with open(name + ".drawio", "w") as f:
            f.write(f'<mxfile><diagram name="{name}"><mxGraphModel background="{BG}"><root>'
                    '<mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(self.cells) +
                    "</root></mxGraphModel></diagram></mxfile>")


def seq(name, parts, msgs, frames=(), notes=()):
    """parts: [(id, label)]; msgs: [(from, to, label, dashed)];
    frames: [(kind, guard, first_row, last_row, [part ids], else_row|None)]; notes: [(row, part, text)]"""
    d = D()
    W, GAP, top, step = 170, 240, 20, 64
    xs = {}
    H = 90 + step * (len(msgs) + 1)
    for i, (pid, label) in enumerate(parts):
        x = 20 + i * GAP
        xs[pid] = x + W / 2
        d.v(label, "shape=umlLifeline;perimeter=lifelinePerimeter;size=48;fontStyle=1;" + (ACCENT if i == 0 else ""), x, top, W, H)
    row_y = lambda i: top + 48 + step * (i + 1)
    for kind, guard, a, b, span, else_row in frames:
        x1 = min(xs[p] for p in span) - 110
        x2 = max(xs[p] for p in span) + 110
        y1 = row_y(a) - 44
        y2 = row_y(b) + 26
        d.v(kind + " [" + guard + "]", "shape=umlFrame;width=220;height=28;align=left;spacingLeft=6;verticalAlign=top;fillColor=none;", x1, y1, x2 - x1, y2 - y1)
        if else_row is not None:
            ye = row_y(else_row) - 36
            d.pe(x1, ye, x2, ye, "", "endArrow=none;dashed=1;")
    for i, (a, b, label, dashed) in enumerate(msgs):
        y = row_y(i)
        st = "endArrow=block;endFill=1;endSize=9;verticalAlign=bottom;" + ("dashed=1;endArrow=open;" if dashed else "")
        if a == b:
            x = xs[a]
            d.pe(x, y - 14, x, y + 14, label, st + "align=left;verticalAlign=middle;spacingLeft=56;", pts=[(x + 44, y - 14), (x + 44, y + 14)])
        else:
            d.pe(xs[a], y, xs[b], y, label, st)
    for row, pid, text in notes:
        d.v(text, "shape=note;size=12;" + DATA, xs[pid] + 16, row_y(row) - 20, 280, 40)
    d.save(name)


def uc(name, actors, case, includes, side=()):
    """One use case. Actors left, the case centre, included cases right, side actors far right."""
    d = D()
    ASTEP, ISTEP = 170, 110
    span = max((len(actors) - 1) * ASTEP, (len(includes) - 1) * ISTEP)
    cy = 60 + span / 2
    cu = d.v(case, "ellipse;fontStyle=1;" + ACCENT, 260, cy - 40, 260, 80)
    a0 = cy - (len(actors) - 1) * ASTEP / 2
    for k, label in enumerate(actors):
        a = d.v(label, ACTOR, 80, a0 + k * ASTEP - 50, 40, 70)
        d.e(a, cu, "", "endArrow=none;")
    i0 = cy - (len(includes) - 1) * ISTEP / 2
    for k, label in enumerate(includes):
        c = d.v(label, "ellipse;", 700, i0 + k * ISTEP - 34, 280, 68)
        d.e(cu, c, "«include»", "dashed=1;endArrow=open;endSize=10;labelPosition=center;")
        for idx, slabel in side:
            if idx == k:
                s = d.v(slabel, ACTOR, 1080, i0 + k * ISTEP - 50, 40, 70)
                d.e(c, s, "", "endArrow=none;")
    d.save(name)


def grid(name, nodes, edges, boxes=(), cw=280, rh=150, w=220, h=64):
    """nodes: [(id, label, style, col, row)] placed centred in a cw x rh grid cell;
    edges: [(src, tgt, label, extra)]; boxes: [(label, col0, row0, col1, row1)] drawn behind."""
    d = D()
    ids = {}
    cx = lambda c: 40 + c * cw + cw / 2
    cy = lambda r: 60 + r * rh + rh / 2
    for box in boxes:
        bid, label, c0, r0, c1, r1 = box if len(box) == 6 else (None,) + tuple(box)
        x0 = cx(c0) - w / 2 - 24
        y0 = cy(r0) - h / 2 - 44
        x1 = cx(c1) + w / 2 + 24
        y1 = cy(r1) + h / 2 + 24
        b = d.v(label, "rounded=1;arcSize=4;verticalAlign=top;align=left;spacingLeft=12;spacingTop=8;fontStyle=1;" + BOX, x0, y0, x1 - x0, y1 - y0)
        if bid:
            ids[bid] = b
    for nid, label, style, c, r in nodes:
        ids[nid] = d.v(label, "rounded=1;" + style, cx(c) - w / 2, cy(r) - h / 2, w, h)
    for ed in edges:
        src, tgt, label = ed[:3]
        extra = ed[3] if len(ed) > 3 else ""
        d.e(ids[src], ids[tgt], label, "edgeStyle=orthogonalEdgeStyle;rounded=1;endArrow=block;endFill=1;endSize=9;" + extra)
    d.save(name)


def cls(name, classes, rels, cw=420, rh=260):
    """classes: [(id, title, stereotype|None, [lines], col, row)] in a grid; rels: [(a, b, label, kind, extra)]."""
    d = D()
    ids = {}
    for cid, title, stereo, lines, c, r in classes:
        head = ("&lt;&lt;" + stereo + "&gt;&gt;<br>" if stereo else "") + "<b>" + title + "</b>"
        label = head + ("<hr>" + "<br>".join(lines) if lines else "")
        h = 40 + (18 if stereo else 0) + (len(lines) * 21 + 16 if lines else 0)
        style = "rounded=0;align=left;verticalAlign=top;spacingLeft=10;spacingTop=6;fontSize=14;" + (ACCENT if stereo in ("interface", "trait") else "")
        ids[cid] = d.v(label, style, 40 + c * cw, 40 + r * rh, cw - 80, h)
    kinds = {
        "comp": "startArrow=diamondThin;startFill=1;startSize=16;endArrow=open;endSize=10;",
        "assoc": "endArrow=open;endSize=10;",
        "dep": "endArrow=open;dashed=1;endSize=10;",
        "impl": "endArrow=block;endFill=0;dashed=1;endSize=12;",
    }
    for rel in rels:
        a, b, label, kind = rel[:4]
        extra = rel[4] if len(rel) > 4 else ""
        d.e(ids[a], ids[b], label, "edgeStyle=orthogonalEdgeStyle;rounded=1;" + kinds[kind] + extra)
    d.save(name)
