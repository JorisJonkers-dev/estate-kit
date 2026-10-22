"""The diagram vocabulary specs.py and metamodels.py declare diagrams in.

Each declaration becomes a source draw.io lays out itself, so no coordinate is written by hand:

- Sequences, state machines and class diagrams are written as Mermaid. draw.io converts them into
  its native UML shapes (lifelines, states with initial and final pseudostates, class boxes sized
  to their members) and lays them out.
- Everything else is written as draw.io XML in draw.io's own components (actors and a system
  boundary, C4 people, systems and containers, cylinders for stores, notes for artifacts,
  containers for nodes and boundaries) and laid out by draw.io's ELK layered layout.

build.py turns the sources into src/*.drawio and png/*.png. Colours are light-dark() pairs, so a
diagram reads in both themes; the PNGs are exported dark.
"""

from __future__ import annotations

import html
import json
from dataclasses import dataclass, field

INK = "light-dark(#1a1a1a,#e8e8e8)"
LINE = "light-dark(#666666,#a8a8a8)"
PAPER = "light-dark(#ffffff,#1e1e1e)"

# (fill, stroke) per tone.
TONES = {
    "plain": ("light-dark(#f5f5f5,#2b2b2b)", "light-dark(#666666,#a8a8a8)"),
    "accent": ("light-dark(#dae8fc,#1f3a5f)", "light-dark(#6c8ebf,#7aa7e0)"),
    "data": ("light-dark(#fff2cc,#3a3220)", "light-dark(#d6b656,#c9a74a)"),
    "good": ("light-dark(#d5e8d4,#21402a)", "light-dark(#82b366,#7fc08c)"),
    "bad": ("light-dark(#f8cecc,#4a2525)", "light-dark(#b85450,#d47a7a)"),
    "warn": ("light-dark(#ffe6cc,#4a3820)", "light-dark(#d79b00,#d9a050)"),
    "external": ("light-dark(#eeeeee,#303030)", "light-dark(#999999,#8a8a8a)"),
}
# Mermaid cannot write light-dark(), so a tone goes in as a sentinel colour that build.py swaps
# for the tone's pair: #0000aN is a fill, #0000bN its stroke.
SENTINELS = {tone: (f"#0000a{i}", f"#0000b{i}") for i, tone in enumerate(TONES)}

FONT = "fontFamily=Helvetica;fontSize=14;"
TEXT = f"html=1;whiteSpace=wrap;{FONT}fontColor={INK};"


@dataclass
class Diagram:
    name: str
    title: str
    fmt: str  # "mmd" or "drawio"
    text: str
    layout: str | None = None  # a --layout argument for draw.io, run after any Mermaid conversion


DIAGRAMS: dict[str, Diagram] = {}


def register(diagram: Diagram) -> None:
    if diagram.name in DIAGRAMS:
        raise ValueError(f"{diagram.name} is declared twice")
    DIAGRAMS[diagram.name] = diagram


# ---------------------------------------------------------------------------------------------
# Mermaid: sequences, state machines, class diagrams.
# ---------------------------------------------------------------------------------------------


def mm(text: str) -> str:
    """Text safe inside a Mermaid label."""
    return text.replace("<", "#lt;").replace(">", "#gt;").replace(";", "#59;")


def tone_defs(tones: dict[str, str]) -> list[str]:
    used = sorted(set(tones.values()))
    return [f"    classDef {t} fill:{SENTINELS[t][0]},stroke:{SENTINELS[t][1]}" for t in used]


def sequence(name: str, title: str, participants: list[tuple[str, str]], steps: list) -> None:
    """participants: [(id, label)], an id starting with "@" is drawn as an actor.
    steps: (from, to, label) a call, (from, to, label, "reply") a reply,
    ("note", participant, text), ("alt", guard, [steps], else_guard, [steps]),
    ("opt", guard, [steps]), ("loop", guard, [steps])."""
    lines = ["sequenceDiagram", "    autonumber"]
    for pid, label in participants:
        kind = "actor" if pid.startswith("@") else "participant"
        lines.append(f"    {kind} {pid.lstrip('@')} as {mm(label)}")

    def emit(items: list, depth: int) -> None:
        pad = "    " * depth
        for step in items:
            head = step[0]
            if head == "note":
                lines.append(f"{pad}Note right of {step[1].lstrip('@')}: {mm(step[2])}")
            elif head == "alt":
                lines.append(f"{pad}alt {mm(step[1])}")
                emit(step[2], depth + 1)
                lines.append(f"{pad}else {mm(step[3])}")
                emit(step[4], depth + 1)
                lines.append(f"{pad}end")
            elif head in ("opt", "loop"):
                lines.append(f"{pad}{head} {mm(step[1])}")
                emit(step[2], depth + 1)
                lines.append(f"{pad}end")
            else:
                a, b, label = (s.lstrip("@") for s in step[:3])
                arrow = "-->>" if len(step) > 3 and step[3] == "reply" else "->>"
                lines.append(f"{pad}{a}{arrow}{b}: {mm(label)}")

    emit(steps, 1)
    register(Diagram(name, title, "mmd", "\n".join(lines) + "\n"))


def states(name: str, title: str, transitions: list[tuple[str, str, str]],
           labels: dict[str, str] | None = None, tones: dict[str, str] | None = None) -> None:
    """transitions: [(from, to, event)], "[*]" is the initial or final pseudostate.
    labels: {id: shown name} for states whose name has spaces. tones: {id: tone}."""
    labels, tones = labels or {}, tones or {}
    lines = ["stateDiagram-v2", "    direction TB"]
    for sid, label in labels.items():
        lines.append(f'    state "{mm(label)}" as {sid}')
    for a, b, event in transitions:
        lines.append(f"    {a} --> {b}" + (f": {mm(event)}" if event else ""))
    lines += tone_defs(tones)
    lines += [f"    class {sid} {tone}" for sid, tone in tones.items()]
    # Mermaid's own layout crowds labels on a cycle, so ELK lays the converted states out again.
    register(Diagram(name, title, "mmd", "\n".join(lines) + "\n", elk("DOWN", 50, 70)))


# Relation kinds in Mermaid's class syntax, written from the owning or depending class.
RELATIONS = {
    "comp": "*--",  # composition: the first owns the second
    "agg": "o--",
    "assoc": "-->",
    "dep": "..>",  # dependency: the first uses the second
    "inherit": "--|>",  # the first specialises the second
    "impl": "..|>",  # the first implements the second
}


def classes(name: str, title: str, members: list[tuple[str, str | None, list[str]]],
            relations: list[tuple], tones: dict[str, str] | None = None,
            direction: str = "TB", notes: tuple | list = ()) -> None:
    """members: [(class, stereotype or None, [member lines])]; a line with "(" is an operation.
    relations: [(a, b, kind, label="", multiplicity at b="")]. notes: [(class, text)], a note
    with no class stands alone."""
    tones = tones or {}
    lines = ["classDiagram", f"    direction {direction}"]
    for cname, stereo, body in members:
        lines.append(f"    class {cname} {{")
        if stereo:
            lines.append(f"        <<{stereo}>>")
        for line in body:
            lines.append(f"        {mm_member(line)}")
        lines.append("    }")
    for rel in relations:
        a, b, kind = rel[:3]
        label = rel[3] if len(rel) > 3 else ""
        mult = rel[4] if len(rel) > 4 else ""
        target = f'"{mult}" {b}' if mult else b
        lines.append(f"    {a} {RELATIONS[kind]} {target}" + (f" : {mm(label)}" if label else ""))
    for cname, text in notes:
        lines.append(f'    note for {cname} "{mm(text)}"' if cname else f'    note "{mm(text)}"')
    lines += tone_defs(tones)
    lines += [f"    class {cname}:::{tone}" for cname, tone in tones.items()]
    register(Diagram(name, title, "mmd", "\n".join(lines) + "\n"))


def mm_member(line: str) -> str:
    """A class member with nothing Mermaid reads as syntax. Angle brackets go in as entity codes,
    which Mermaid's class parser can leave half-decoded; build.py finishes the job."""
    out = line.replace("{", "(").replace("}", ")").replace(";", ",").replace('"', "'")
    return out.replace("<", "#lt;").replace(">", "#gt;")


# ---------------------------------------------------------------------------------------------
# draw.io XML laid out by ELK: use cases, C4, deployment, flows and component graphs.
# ---------------------------------------------------------------------------------------------


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def size(label: str, lo: int = 160, hi: int = 240, per_line: float = 7.6, line_h: int = 20, pad: int = 26) -> tuple[int, int]:
    """A box wide enough for its label, wrapping past hi, and tall enough for the wrapped lines."""
    plain = label.replace("<br>", "\n")
    longest = max(len(part) for part in plain.split("\n"))
    w = int(min(hi, max(lo, longest * per_line + 40)))
    chars = max(1, int((w - 24) / per_line))
    lines = sum(max(1, -(-len(part) // chars)) for part in plain.split("\n"))
    return w, max(56, lines * line_h + pad)


def elk(direction: str = "RIGHT", node: int = 40, layer: int = 90, wrap: bool = False) -> str:
    extra = {"elk.layered.wrapping.strategy": "MULTI_EDGE", "elk.aspectRatio": 1.6} if wrap else {}
    return json.dumps([{
        "layout": "elkLayered",
        "config": {
            **extra,
            "elk.layered.crossingMinimization.forceNodeModelOrder": True,
            "elk.direction": direction,
            "elk.spacing.nodeNode": node,
            "elk.layered.spacing.nodeNodeBetweenLayers": layer,
            "elk.spacing.edgeLabel": 6,
            "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
            "elk.layered.considerModelOrder.strategy": "NODES_AND_EDGES",
            "elk.hierarchyHandling": "INCLUDE_CHILDREN",
            "elk.nodeSize.constraints": "",
            "edgeStyle": "orthogonal",
            "corners": "rounded",
        },
    }], separators=(",", ":"))


EDGES = {
    "flow": "endArrow=block;endFill=1;endSize=8;",
    "dashed": "endArrow=open;endSize=10;dashed=1;",
    "assoc": "endArrow=none;",
    "include": "endArrow=open;endSize=10;dashed=1;",
    "both": "startArrow=block;startFill=1;endArrow=block;endFill=1;endSize=8;startSize=8;",
}


@dataclass
class Graph:
    """A diagram of shapes and edges in draw.io's own components, laid out by ELK."""

    name: str
    title: str
    direction: str = "RIGHT"
    node_gap: int = 40
    layer_gap: int = 90
    placed: bool = False  # True: every shape is given its position, and ELK is not run
    wrap: bool = False  # True: a long chain wraps into rows instead of running off to one side
    cells: list[str] = field(default_factory=list)
    ids: set[str] = field(default_factory=set)
    edge_count: int = 0

    def _vertex(self, cid: str, label: str, style: str, w: int, h: int, parent: str | None) -> str:
        if cid in self.ids:
            raise ValueError(f"{self.name}: {cid} is declared twice")
        self.ids.add(cid)
        self.cells.append(
            f'<mxCell id="{cid}" value="{esc(label)}" style="{style}" vertex="1" parent="{parent or "1"}">'
            f'<mxGeometry width="{w}" height="{h}" as="geometry"/></mxCell>')
        return cid

    def _toned(self, tone: str) -> str:
        fill, stroke = TONES[tone]
        return f"fillColor={fill};strokeColor={stroke};"

    # Shapes.
    def box(self, cid: str, label: str, tone: str = "plain", parent: str | None = None) -> str:
        """A process, service or step."""
        w, h = size(label)
        return self._vertex(cid, label, f"rounded=1;arcSize=10;{TEXT}{self._toned(tone)}", w, h, parent)

    def store(self, cid: str, label: str, tone: str = "data", parent: str | None = None) -> str:
        """Something that keeps state: a database, a registry, a cache."""
        w, h = size(label, lo=150, pad=40)
        return self._vertex(cid, label, f"shape=cylinder3;size=10;boundedLbl=1;backgroundOutline=1;{TEXT}{self._toned(tone)}", w, h + 14, parent)

    def artifact(self, cid: str, label: str, tone: str = "data", parent: str | None = None) -> str:
        """A file, document or model passed between steps."""
        w, h = size(label)
        return self._vertex(cid, label, f"shape=note;size=14;{TEXT}{self._toned(tone)}", w, h, parent)

    def package(self, cid: str, label: str, tone: str = "plain", parent: str | None = None) -> str:
        """A crate or package."""
        w, h = size(label, lo=150)
        return self._vertex(cid, label, f"shape=folder;tabWidth=50;tabHeight=12;tabPosition=left;spacingTop=8;{TEXT}{self._toned(tone)}", w, h + 12, parent)

    def actor(self, cid: str, label: str, parent: str | None = None) -> str:
        return self._vertex(cid, label, f"shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;outlineConnect=0;{TEXT}"
                            f"fillColor={PAPER};strokeColor={LINE};", 40, 76, parent)

    def usecase(self, cid: str, label: str, tone: str = "plain", parent: str | None = None) -> str:
        w, h = size(label, lo=200, hi=260)
        return self._vertex(cid, label, f"ellipse;{TEXT}{self._toned(tone)}", w + 20, h + 14, parent)

    def decision(self, cid: str, label: str, parent: str | None = None) -> str:
        w, _ = size(label, lo=180)
        return self._vertex(cid, label, f"rhombus;{TEXT}{self._toned('plain')}", w + 20, 90, parent)

    def terminal(self, cid: str, label: str, tone: str = "plain", parent: str | None = None) -> str:
        """A start or an end in a flow."""
        w, h = size(label)
        return self._vertex(cid, label, f"rounded=1;arcSize=50;{TEXT}{self._toned(tone)}", w, h, parent)

    def group(self, cid: str, label: str, kind: str = "boundary", parent: str | None = None) -> str:
        """A container: a system boundary, a deployment node, or a trust boundary."""
        stroke = {"boundary": LINE, "node": LINE, "trust": "light-dark(#b85450,#d47a7a)"}[kind]
        dash = "dashed=1;dashPattern=8 4;" if kind in ("boundary", "trust") else ""
        style = (f"swimlane;startSize=30;rounded=1;arcSize=4;absoluteArcSize=1;container=1;collapsible=0;{dash}"
                 f"{TEXT}fontStyle=1;fillColor=none;swimlaneFillColor=none;strokeColor={stroke};")
        return self._vertex(cid, label, style, 300, 200, parent)

    # C4.
    def person(self, cid: str, name: str, description: str, parent: str | None = None) -> str:
        label = f"<b>{esc(name)}</b><div style=\"font-size:11px\">[Person]</div><div>{esc(description)}</div>"
        style = ("shape=mxgraph.c4.person2;html=1;whiteSpace=wrap;fontFamily=Helvetica;fontSize=12;align=center;"
                 "verticalAlign=bottom;spacingBottom=6;fillColor=#08427B;strokeColor=#073B6F;fontColor=#ffffff;")
        return self._raw_vertex(cid, label, style, 200, 170, parent)

    def system(self, cid: str, name: str, description: str, kind: str = "system", tech: str = "",
               parent: str | None = None) -> str:
        """kind: system (in scope), external, container, database."""
        colours = {
            "system": ("#1168BD", "#0B4884"),
            "external": ("#8C8496", "#736782"),
            "container": ("#438DD5", "#3C7FC0"),
            "database": ("#438DD5", "#3C7FC0"),
        }[kind]
        tag = {"system": "Software System", "external": "Software System", "container": "Container",
               "database": "Container"}[kind]
        tag = f"{tag}: {tech}" if tech else tag
        label = f"<b>{esc(name)}</b><div style=\"font-size:11px\">[{esc(tag)}]</div><div>{esc(description)}</div>"
        shape = "shape=cylinder3;size=12;boundedLbl=1;" if kind == "database" else "rounded=1;arcSize=8;"
        style = (f"{shape}html=1;whiteSpace=wrap;fontFamily=Helvetica;fontSize=12;align=center;"
                 f"fillColor={colours[0]};strokeColor={colours[1]};fontColor=#ffffff;")
        return self._raw_vertex(cid, label, style, 240, 130 if kind == "database" else 120, parent)

    def _raw_vertex(self, cid: str, label_html: str, style: str, w: int, h: int, parent: str | None) -> str:
        if cid in self.ids:
            raise ValueError(f"{self.name}: {cid} is declared twice")
        self.ids.add(cid)
        self.cells.append(
            f'<mxCell id="{cid}" value="{esc(label_html)}" style="{style}" vertex="1" parent="{parent or "1"}">'
            f'<mxGeometry width="{w}" height="{h}" as="geometry"/></mxCell>')
        return cid

    def c4_edge(self, a: str, b: str, description: str, tech: str = "") -> None:
        label = f"<b>{esc(description)}</b>" + (f"<div style=\"font-size:11px\">[{esc(tech)}]</div>" if tech else "")
        self._edge(a, b, label, EDGES["flow"] + "dashed=1;dashPattern=6 4;")

    # Edges.
    def edge(self, a: str, b: str, label: str = "", kind: str = "flow") -> None:
        self._edge(a, b, label, EDGES[kind])

    def _edge(self, a: str, b: str, label: str, style: str) -> None:
        for end in (a, b):
            if end not in self.ids:
                raise ValueError(f"{self.name}: edge names {end}, which is not declared")
        self.edge_count += 1
        self.cells.append(
            f'<mxCell id="e{self.edge_count}" value="{esc(label)}" style="html=1;rounded=1;{FONT}fontSize=12;'
            f'fontColor={INK};strokeColor={LINE};labelBackgroundColor={PAPER};{style}" edge="1" parent="1" '
            f'source="{a}" target="{b}"><mxGeometry relative="1" as="geometry"/></mxCell>')

    def uml_class(self, cid: str, name: str, members: list[str], x: int, y: int, w: int = 220,
                  stereotype: str | None = None, tone: str = "plain") -> str:
        """draw.io's own UML class: a header and one row per member, at a given position."""
        head = (f"«{stereotype}»<br>" if stereotype else "") + f"<b>{esc(name)}</b>"
        start = 44 if stereotype else 28
        rows = members or [""]
        h = start + 22 * len(rows) + 8
        self.ids.add(cid)
        fill, stroke = TONES[tone]
        self.cells.append(
            f'<mxCell id="{cid}" value="{esc(head)}" style="swimlane;childLayout=stackLayout;horizontal=1;startSize={start};'
            f'horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=0;marginBottom=8;'
            f'{TEXT}fillColor={fill};swimlaneFillColor={fill};strokeColor={stroke};" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        for i, member in enumerate(rows):
            self.cells.append(
                f'<mxCell id="{cid}-{i}" value="{esc(member)}" style="text;html=1;{FONT}fontSize=13;fontColor={INK};'
                f'strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=8;overflow=hidden;'
                f'rotatable=0;" vertex="1" parent="{cid}">'
                f'<mxGeometry y="{start + 22 * i}" width="{w}" height="22" as="geometry"/></mxCell>')
        return cid

    def generalize(self, child: str, parent: str, route: list[tuple[float, float]] = (), exit_y: float = 0.5) -> None:
        """A generalization along the given waypoints, so many of them can share one trunk
        (UML's shared target style) through the gaps between boxes."""
        self.edge_count += 1
        points = "".join(f'<mxPoint x="{x:g}" y="{y:g}"/>' for x, y in route)
        self.cells.append(
            f'<mxCell id="e{self.edge_count}" value="" style="html=1;edgeStyle=none;rounded=0;strokeColor={LINE};'
            f'endArrow=block;endFill=0;endSize=14;exitX=0;exitY={exit_y:g};exitDx=0;exitDy=0;entryX=0.5;entryY=1;'
            f'entryDx=0;entryDy=0;" edge="1" parent="1" source="{child}" target="{parent}">'
            f'<mxGeometry relative="1" as="geometry"><Array as="points">{points}</Array></mxGeometry></mxCell>')

    def done(self) -> None:
        xml = ('<mxfile><diagram name="' + esc(self.name) + '"><mxGraphModel><root>'
               '<mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(self.cells) +
               "</root></mxGraphModel></diagram></mxfile>\n")
        layout = None if self.placed else elk(self.direction, self.node_gap, self.layer_gap, self.wrap)
        register(Diagram(self.name, self.title, "drawio", xml, layout))


def use_case(name: str, title: str, actors: list[str], case: str, includes: list[str],
             secondary: tuple | list = (), system: str = "estate-kit") -> None:
    """One use case: primary actors on the left, the case and the cases it includes inside the
    system boundary, and secondary actors on the right, joined to the included case they serve."""
    g = Graph(name, title)
    g.group("sys", system)
    for i, label in enumerate(actors):
        g.actor(f"a{i}", label)
    g.usecase("uc", case, tone="accent", parent="sys")
    for i, label in enumerate(includes):
        g.usecase(f"i{i}", label, parent="sys")
    for i in range(len(actors)):
        g.edge(f"a{i}", "uc", kind="assoc")
    for i in range(len(includes)):
        g.edge("uc", f"i{i}", "«include»", kind="include")
    for k, (index, label) in enumerate(secondary):
        g.actor(f"s{k}", label)
        g.edge(f"i{index}", f"s{k}", kind="assoc")
    g.done()


# ---------------------------------------------------------------------------------------------
# Sources on disk.
# ---------------------------------------------------------------------------------------------


def source(diagram: Diagram) -> str:
    """The file build.py reads: the source with its title, and for XML its layout, attached."""
    if diagram.fmt == "mmd":
        layout = f"%% layout: {diagram.layout}\n" if diagram.layout else ""
        return f"%% title: {diagram.title}\n{layout}" + diagram.text
    head = f'<mxfile title="{esc(diagram.title)}" layout="{esc(diagram.layout or "")}">'
    return diagram.text.replace("<mxfile>", head, 1)


def write_all(directory: str) -> None:
    import os

    os.makedirs(directory, exist_ok=True)
    for diagram in DIAGRAMS.values():
        with open(os.path.join(directory, f"{diagram.name}.{diagram.fmt}"), "w", encoding="utf-8") as f:
            f.write(source(diagram))
