#!/usr/bin/env python3
"""Regenerate the power tree from power_tree.json (single source of truth).

Outputs:
  - kicad/powertree.kicad_sch : boxes-and-arrows tree, left-to-right,
    wrapping to a new band if it outgrows the sheet width
  - kicad/supply.kicad_sch    : per-stage load annotations (near stages)

Managed elements are tracked by UUID in kicad/power_tree_gen.json and
replaced wholesale on each run; hand-drawn content is left untouched.
The Power Tree sheet must already exist in the root hierarchy.
"""
import json, uuid, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KI = os.path.join(ROOT, 'kicad')
SRC = os.path.join(ROOT, 'power_tree.json')
STATE = os.path.join(KI, 'power_tree_gen.json')
TREE_SCH = os.path.join(KI, 'powertree.kicad_sch')
SUPPLY_SCH = os.path.join(KI, 'supply.kicad_sch')

G = 1.27
def pt(n): return round(n * G, 4)
def U(): return str(uuid.uuid4())

# layout (grid units); A4 landscape drawable ~ x 12..220, y 12..150
X0, Y0 = 10, 16
BOX_W = 46
COL_GAP = 8
LINE = 2.2
PAD = 1.2
ROW_GAP = 4
X_MAX = 222          # wrap when a column would start past this
BAND_GAP = 6

def strip_managed(sch, old):
    out, i = [], 0
    while i < len(sch):
        j = sch.find('(uuid "', i)
        if j == -1:
            out.append(sch[i:]); break
        k = sch.rfind('\n  (', i, j)
        if k == -1:
            out.append(sch[i:j + 7]); i = j + 7; continue
        uid = sch[j + 7:sch.find('"', j + 7)]
        depth = 0; e = k + 1
        for e in range(k + 1, len(sch)):
            if sch[e] == '(': depth += 1
            elif sch[e] == ')':
                depth -= 1
                if depth == 0: break
        kind = sch[k + 1:e + 1].split('(', 2)[1].split()[0]
        if uid in old and kind in ('rectangle', 'polyline', 'text'):
            out.append(sch[i:k]); i = e + 1
        else:
            out.append(sch[i:e + 1]); i = e + 1
    return ''.join(out)

class Emit:
    def __init__(self):
        self.items, self.uuids = [], []
    def rect(self, x1, y1, x2, y2):
        u = U(); self.uuids.append(u)
        self.items.append(f'  (rectangle (start {pt(x1)} {pt(y1)}) (end {pt(x2)} {pt(y2)})'
                          f' (stroke (width 0.1524) (type solid)) (fill (type none)) (uuid "{u}"))')
    def line(self, pts_):
        u = U(); self.uuids.append(u)
        coords = ' '.join(f'(xy {pt(x)} {pt(y)})' for x, y in pts_)
        self.items.append(f'  (polyline (pts {coords}) (stroke (width 0.1524) (type solid)) (uuid "{u}"))')
    def text(self, t, x, y, size=1.27, bold=False):
        u = U(); self.uuids.append(u)
        b = ' (bold yes)' if bold else ''
        t = t.replace('"', "'")
        self.items.append(f'  (text "{t}" (exclude_from_sim no) (at {pt(x)} {pt(y)} 0)'
                          f' (effects (font (size {size} {size}){b}) (justify left bottom)) (uuid "{u}"))')

def node_lines(name, src, nodes):
    inp = src['input']
    if name == inp['name']:
        lines = [f"{inp['name']}  {inp['desc']}", inp['protection']]
        if inp.get('note'): lines.append(inp['note'])
        return lines
    n = nodes[name]
    hdr = n['name']
    if n.get('converter'): hdr += '  <- ' + n['converter']
    lines = [hdr]
    if n.get('budget'): lines.append('budget: ' + n['budget'])
    if n.get('note'): lines.append(n['note'])
    for ld in n.get('loads', []):
        lines.append(f"  - {ld['name']}: {ld['ma']} mA")
    return lines

def main():
    src = json.load(open(SRC))
    nodes = {n['name']: n for n in src['nodes']}
    children = {}
    for n in src['nodes']:
        children.setdefault(n['from'], []).append(n['name'])
    inp_name = src['input']['name']

    e = Emit()
    e.text('POWER TREE  (generated from power_tree.json -- do not hand-edit)', X0, Y0 - 2, size=1.778, bold=True)

    # left-to-right layout: recursive; each node placed at (x, y); children in
    # the next column, stacked; a subtree that would start past X_MAX wraps to
    # a new band below everything placed so far.
    band_bottom = [Y0]

    def place(name, x, y):
        """Place node and subtree; returns (bottom_y_of_subtree, box_geom)."""
        if x > X_MAX - BOX_W:
            # wrap: new band at left margin, below everything so far
            y = band_bottom[0] + BAND_GAP
            x = X0
        lines = node_lines(name, src, nodes)
        h = 2 * PAD + LINE * len(lines)
        e.rect(x, y, x + BOX_W, y + h)
        ty = y + PAD + LINE * 0.85
        for i, ln in enumerate(lines):
            e.text(ln, x + PAD, ty + LINE * i, bold=(i == 0))
        band_bottom[0] = max(band_bottom[0], y + h)
        geom = (x, y, x + BOX_W, y + h)
        cy = y
        sub_bottom = y + h
        for c in children.get(name, []):
            cb, cgeom = place(c, x + BOX_W + COL_GAP, cy)
            # arrow: parent right edge -> child left edge
            pcy = (geom[1] + geom[3]) / 2
            kcy = (cgeom[1] + cgeom[3]) / 2
            midx = (geom[2] + cgeom[0]) / 2
            if cgeom[0] > geom[2]:      # same band, child to the right
                e.line([(geom[2], pcy), (midx, pcy), (midx, kcy), (cgeom[0], kcy)])
                e.line([(cgeom[0] - 1.6, kcy - 0.8), (cgeom[0], kcy), (cgeom[0] - 1.6, kcy + 0.8)])
            else:                        # wrapped band: drop from parent bottom
                e.line([( (geom[0]+geom[2])/2, geom[3]), ((geom[0]+geom[2])/2, cgeom[1] - 2),
                        (cgeom[0] - 3, cgeom[1] - 2), (cgeom[0] - 3, kcy), (cgeom[0], kcy)])
                e.line([(cgeom[0] - 1.6, kcy - 0.8), (cgeom[0], kcy), (cgeom[0] - 1.6, kcy + 0.8)])
            cy = cb + ROW_GAP
            sub_bottom = max(sub_bottom, cb)
        return sub_bottom, geom

    place(inp_name, X0, Y0)

    # per-stage annotations on the supply sheet
    s_notes = Emit()
    for n in src['nodes']:
        if n.get('sch_note') and n.get('sch_note_at'):
            x, yy = n['sch_note_at']
            for i, ln in enumerate(reversed(n['sch_note'].split('\n'))):
                s_notes.text(ln, x, yy - 2 * i)

    # ---- apply to files, replacing previously managed elements ----
    old = set()
    if os.path.exists(STATE):
        st = json.load(open(STATE))
        old = set(st.get('uuids', []) + st.get('supply', []) + st.get('powertree', []))

    for path, emit in ((TREE_SCH, e), (SUPPLY_SCH, s_notes)):
        sch = strip_managed(open(path).read(), old)
        tail = sch.rstrip()
        assert tail.endswith(')')
        sch = tail[:-1] + '\n'.join(emit.items) + '\n)\n'
        open(path, 'w').write(sch)

    json.dump({'powertree': e.uuids, 'supply': s_notes.uuids}, open(STATE, 'w'), indent=0)
    print(f'power tree: {len(e.items)} elements -> powertree.kicad_sch; '
          f'{len(s_notes.items)} notes -> supply.kicad_sch')

if __name__ == '__main__':
    main()
