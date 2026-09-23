"""
mini_kit — parts for the map miniatures, built on `mini.Mini`.
Every placer takes a ground function g(x, y) (local map units around the landmark's anchor)
and sits the part on the terrain, sinking foundations so slopes never show gaps.
"""
import math
import random
from math import sin, cos, pi, atan2, hypot

from mini import PAL, Mini, shade, mix

GLOW, WATER, GOLD = 1, 2, 3
SEA = 0.03  # water surface height on the website


def footprint_z(g, x, y, w, d, rot=0.0):
    c, s = cos(rot), sin(rot)
    zs = [g(x + c * px - s * py, y + s * px + c * py) for px, py in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2), (0, 0))]
    return min(zs), max(zs)


def P(name):
    return PAL[name] if isinstance(name, str) else name


# ------------------------------------------------------------------------------------------ buildings
def hall(m, g, x, y, w, d, rot=0.0, h=None, roof="roof", walls="red", plat="stone", double=False, plat_h=None, roof_h=None, z=None):
    """A timber hall on a stone platform with a hip roof (double eaves for the grandest halls). Returns top z."""
    h = h if h is not None else 0.45 * d
    zmin, zmax = footprint_z(g, x, y, w * 1.15, d * 1.2, rot) if z is None else (z, z)
    ph = plat_h if plat_h is not None else 0.05 + 0.08 * d
    m.box(x, y, zmin - 0.3, w * 1.15, d * 1.2, (zmax - zmin) + 0.3 + ph, P(plat), rot, top=shade(P(plat), 1.1))
    z0 = zmax + ph
    bw, bd = w * 0.84, d * 0.74
    m.box(x, y, z0, bw, bd, h, P(walls), rot)
    # a lighter band of lattice windows under the eaves
    m.box(x, y, z0 + h * 0.62, bw * 1.004, bd * 1.004, h * 0.2, shade(P("wood_light"), 1.0), rot)
    rh = roof_h if roof_h is not None else 0.5 * d
    if double:
        m.roof(x, y, z0 + h * 0.72, w * 1.02, d * 1.02, rh * 0.28, P(roof), rot, over=0.16 * d, lift=rh * 0.12, ridge=None, nv=2, ridge_color=False)
        m.box(x, y, z0 + h * 0.72, bw * 0.8, bd * 0.8, h * 0.55, P(walls), rot)
        m.roof(x, y, z0 + h * 1.25, w * 0.86, d * 0.86, rh, P(roof), rot, over=0.2 * d)
        return z0 + h * 1.25 + rh
    m.roof(x, y, z0 + h, w, d, rh, P(roof), rot, over=0.2 * d)
    return z0 + h + rh


def house(m, g, x, y, w, d, rot=0.0, walls="white", roof="roof", h=None):
    h = h if h is not None else 0.55 * d
    zmin, zmax = footprint_z(g, x, y, w, d, rot)
    m.box(x, y, zmin - 0.2, w * 0.9, d * 0.82, (zmax - zmin) + 0.2 + h, P(walls), rot)
    m.roof(x, y, zmax + h, w, d, 0.42 * d, P(roof), rot, over=0.12 * d, lift=0.08 * d, nu=2, nv=2, ridge_color=False)


def pagoda(m, g, x, y, r=0.12, tiers=7, th=None, body="white", roof="roof", sides=8, base=True, taper=0.9, rail=None):
    """Tiered masonry pagoda (Liuhe, Leifeng, Kaiyuan's twin towers, the Porcelain Tower)."""
    th = th if th is not None else r * 0.95
    z, _ = footprint_z(g, x, y, r * 3, r * 3)
    if base:
        m.prism(x, y, z - 0.3, r * 1.55, 0.3 + r * 0.35, sides, P("stone"), rot=pi / sides)
        z += r * 0.35
    rr = r
    rot = pi / sides
    for i in range(tiers):
        m.prism(x, y, z, rr, th, sides, P(body), rr * 0.97, rot=rot)
        if rail:
            m.prism(x, y, z + th * 0.05, rr * 1.02, th * 0.18, sides, P(rail), rr * 1.02, rot=rot)
        m.roof_poly(x, y, z + th * 0.92, rr * 1.55, th * 0.38, sides, P(roof), rot=rot, lift=th * 0.22)
        z += th * 1.12
        rr *= taper
    m.prism(x, y, z - th * 0.1, rr * 0.35, th * 0.35, 8, P("gold_dark"), rr * 0.3)
    m.prism(x, y, z + th * 0.2, rr * 0.12, th * 0.9, 6, P("gold_dark"), 0.002)
    return z


def stupa(m, g, x, y, s=0.35, color="stupa"):
    """Tibetan-style bottle stupa, like Dadu's White Stupa (1279)."""
    z, _ = footprint_z(g, x, y, s * 1.6, s * 1.6)
    c = P(color)
    m.box(x, y, z - 0.3, s * 1.5, s * 1.5, 0.3 + s * 0.22, c)
    m.box(x, y, z + s * 0.22, s * 1.25, s * 1.25, s * 0.2, shade(c, 0.97))
    m.box(x, y, z + s * 0.42, s * 1.0, s * 1.0, s * 0.12, c)
    b = z + s * 0.54
    prof = [(s * 0.34, 0), (s * 0.5, s * 0.08), (s * 0.55, s * 0.3), (s * 0.5, s * 0.55), (s * 0.3, s * 0.72), (s * 0.18, s * 0.76)]
    m.lathe(x, y, b, prof, 16, c)
    m.box(x, y, b + s * 0.74, s * 0.34, s * 0.34, s * 0.1, c)
    # thirteen rings of the spire
    m.prism(x, y, b + s * 0.84, s * 0.2, s * 0.78, 12, shade(c, 0.95), s * 0.07)
    m.lathe(x, y, b + s * 1.58, [(0.001, 0), (s * 0.3, s * 0.05), (s * 0.28, s * 0.09), (0.001, s * 0.1)], 12, P("gold_dark"))
    m.prism(x, y, b + s * 1.66, s * 0.05, s * 0.3, 8, P("gold"), 0.004)


def gate(m, g, x, y, w, d, rot=0.0, roof="roof", body="brick_grey", hall_color="red", h=None):
    """City gate: a masonry block pierced by a dark arch, with a timber gate-tower on top."""
    h = h if h is not None else 0.55 * d
    zmin, zmax = footprint_z(g, x, y, w, d, rot)
    m.box(x, y, zmin - 0.3, w, d, zmax - zmin + 0.3 + h, P(body), rot, top=shade(P(body), 1.08))
    c, s = cos(rot), sin(rot)
    for side in (-1, 1):
        ox, oy = -s * side * (d / 2 + 0.002), c * side * (d / 2 + 0.002)
        m.box(x + ox, y + oy, zmax, w * 0.26, 0.004, h * 0.62, P("black"), rot)
    return hall(m, g, x, y, w * 0.78, d * 0.62, rot, h=h * 0.55, roof=roof, walls=hall_color, plat=body, plat_h=0.0, z=zmax + h)


def wall(m, g, pts, h=0.07, t=0.06, color="brick_grey", closed=True, tower_every=0.0, tower=0.1):
    """City wall along a polyline, following the ground; optional bastions."""
    col = P(color)
    n = len(pts)
    segs = n if closed else n - 1
    for i in range(segs):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        L = hypot(x1 - x0, y1 - y0)
        steps = max(1, int(L / 0.25))
        for k in range(steps):
            a = k / steps
            b = (k + 1) / steps
            xa, ya = x0 + (x1 - x0) * a, y0 + (y1 - y0) * a
            xb, yb = x0 + (x1 - x0) * b, y0 + (y1 - y0) * b
            za, zb = g(xa, ya), g(xb, yb)
            zm = min(za, zb)
            m.box((xa + xb) / 2, (ya + yb) / 2, zm - 0.3, hypot(xb - xa, yb - ya) + t, t, abs(za - zb) + 0.3 + h, col,
                  atan2(yb - ya, xb - xa), top=shade(col, 1.12), taper=0.92)
        if tower_every > 0:
            nt = int(L / tower_every)
            for k in range(1, nt):
                a = k / nt
                xa, ya = x0 + (x1 - x0) * a, y0 + (y1 - y0) * a
                z = g(xa, ya)
                m.box(xa, ya, z - 0.3, tower, tower, 0.3 + h * 1.12, col, atan2(y1 - y0, x1 - x0), top=shade(col, 1.12))


def tree(m, g, x, y, s=0.08, kind="broad", seed=0, color=None, z=None):
    rnd = random.Random(seed)
    zg = g(x, y) if z is None else z
    if zg < SEA + 0.01:
        return
    s *= rnd.uniform(0.75, 1.25)
    if kind == "pine":
        m.prism(x, y, zg - 0.05, s * 0.08, s * 0.7 + 0.05, 5, P("trunk"), s * 0.05, cap=False)
        c = P(color or "pine")
        for i in range(3):
            m.prism(x, y, zg + s * (0.35 + 0.42 * i), s * (0.55 - 0.13 * i), s * 0.5, 7, shade(c, 0.9 + 0.08 * i), 0.002, rot=rnd.random())
        return
    if kind == "cypress":
        m.prism(x, y, zg - 0.05, s * 0.3, s * 1.8, 7, P(color or "tree_dark"), s * 0.02, rot=rnd.random())
        return
    if kind == "willow":
        m.prism(x, y, zg - 0.05, s * 0.07, s * 0.6, 5, P("trunk"), s * 0.05, cap=False)
        m.lathe(x, y, zg + s * 0.25, [(s * 0.55, 0), (s * 0.62, s * 0.35), (s * 0.45, s * 0.75), (0.001, s * 0.9)], 7, P(color or "tree_light"))
        return
    if kind == "palm":
        m.prism(x, y, zg - 0.05, s * 0.05, s * 1.3, 5, P("trunk"), s * 0.04, cap=False)
        m.lathe(x, y, zg + s * 1.2, [(0.001, -s * 0.15), (s * 0.55, 0.0), (0.001, s * 0.12)], 7, P(color or "tree"))
        return
    m.prism(x, y, zg - 0.05, s * 0.08, s * 0.5, 5, P("trunk"), s * 0.06, cap=False)
    c = P(color or rnd.choice(["tree", "tree", "tree_dark", "tree_light"]))
    m.sphere(x, y, zg + s * 0.3, s * 0.5, c, n=7, rings=4, sz=0.85, jitter=0.12, seed=seed)


def grove(m, g, cx, cy, r, n, seed=0, kinds=("broad",), s=0.08, avoid=(), ring=0.0):
    """Scatter trees in a disc (or an annulus if ring > 0), skipping water and avoid-rectangles (x0, y0, x1, y1)."""
    rnd = random.Random(seed)
    k = 0
    tries = 0
    while k < n and tries < n * 20:
        tries += 1
        a = rnd.random() * 2 * pi
        rr = r * math.sqrt(rnd.uniform((ring / r) ** 2 if ring else 0.0, 1.0))
        x, y = cx + cos(a) * rr, cy + sin(a) * rr
        if any(x0 < x < x1 and y0 < y < y1 for (x0, y0, x1, y1) in avoid):
            continue
        if g(x, y) < SEA + 0.02:
            continue
        tree(m, g, x, y, s, rnd.choice(kinds), seed=seed * 1000 + k)
        k += 1


def inside(poly, x, y):
    """Point-in-polygon (even-odd)."""
    c = False
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c


def ribbon(m, g, pts, width, color="water", lift=0.012, mat=WATER, floor=SEA + 0.006, step=0.08):
    """A draped strip along a polyline (rivers, canals, roads, causeways)."""
    dense = []
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        n = max(1, int(hypot(x1 - x0, y1 - y0) / step))
        dense += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n)]
    dense.append(pts[-1])
    verts, faces = [], []
    for i, (x, y) in enumerate(dense):
        a = dense[max(i - 1, 0)]
        b = dense[min(i + 1, len(dense) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = max(hypot(dx, dy), 1e-6)
        nx, ny = -dy / L * width / 2, dx / L * width / 2
        for sx in (-1, 1):
            px, py = x + nx * sx, y + ny * sx
            verts.append((px, py, max(g(px, py), g(x, y), floor) + lift))
    for i in range(len(dense) - 1):
        a = 2 * i
        faces.append([a, a + 2, a + 3, a + 1])
    m.mesh(verts, faces, P(color), mat=mat)


def city_blocks(m, g, rect, rot=0.0, seed=0, lot=0.1, street=0.035, fill=0.8, walls=("white", "plaster"), roofs=("roof_house", "roof_house2", "roof_house"), avoid=(), hmin=0.04, within=None):
    """Fill a rectangle (cx, cy, w, d) with rows of houses separated by streets (optionally only inside a polygon)."""
    rnd = random.Random(seed)
    cx, cy, W, D = rect
    c, s = cos(rot), sin(rot)
    nx, ny = int(W / (lot + street)), int(D / (lot * 0.8 + street))
    for i in range(nx):
        for j in range(ny):
            if rnd.random() > fill:
                continue
            lx = -W / 2 + (i + 0.5) * W / nx + rnd.uniform(-0.01, 0.01)
            ly = -D / 2 + (j + 0.5) * D / ny + rnd.uniform(-0.01, 0.01)
            x, y = cx + c * lx - s * ly, cy + s * lx + c * ly
            if any(x0 < x < x1 and y0 < y < y1 for (x0, y0, x1, y1) in avoid):
                continue
            if within is not None and not inside(within, x, y):
                continue
            if g(x, y) < SEA + 0.02:
                continue
            w = lot * rnd.uniform(0.75, 1.0)
            d = lot * rnd.uniform(0.55, 0.75)
            house(m, g, x, y, w, d, rot + (pi / 2 if rnd.random() < 0.15 else 0), rnd.choice(walls), rnd.choice(roofs), h=max(hmin, d * 0.55))


def slab_on_ground(m, g, pts, color, lift=0.012, mat=0, n=10):
    """A ground patch (courtyard, market, field) draped over the terrain as a small grid."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    verts, faces = [], []
    for j in range(n + 1):
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n
            y = y0 + (y1 - y0) * j / n
            verts.append((x, y, g(x, y) + lift))
    for j in range(n):
        for i in range(n):
            a = j * (n + 1) + i
            faces.append([a, a + 1, a + n + 2, a + n + 1])
    m.mesh(verts, faces, P(color), mat=mat)


# ------------------------------------------------------------------------------------------ water & land features
def pond(m, pts, z, color="pond", edge="stone"):
    m.slab(pts, z, P(color), mat=WATER)
    m.slab(pts, z - 0.004, P(edge), thick=0.25)


def bridge(m, x0, y0, x1, y1, z, w=0.05, color="stone", piers=5):
    L = hypot(x1 - x0, y1 - y0)
    a = atan2(y1 - y0, x1 - x0)
    m.box((x0 + x1) / 2, (y0 + y1) / 2, z, L, w, 0.018, P(color), a, top=shade(P(color), 1.1))
    for k in range(piers + 1):
        t = k / piers
        m.box(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z - 0.3, w * 0.6, w * 1.4, 0.3, shade(P(color), 0.85), a)


def paddies(m, g, cx, cy, w, d, rot=0.0, nx=6, ny=4, seed=0, palette=("paddy_water", "paddy", "rice", "paddy")):
    """A block of rice plots with bunds, each plot draped on the ground."""
    rnd = random.Random(seed)
    c, s = cos(rot), sin(rot)
    pw, pd = w / nx, d / ny
    for i in range(nx):
        for j in range(ny):
            lx, ly = -w / 2 + (i + 0.5) * pw, -d / 2 + (j + 0.5) * pd
            x, y = cx + c * lx - s * ly, cy + s * lx + c * ly
            z = g(x, y)
            if z < SEA + 0.02:
                continue
            col = P(rnd.choice(palette))
            hw, hd = pw * 0.44, pd * 0.42
            pts = [(x + c * ax - s * ay, y + s * ax + c * ay) for ax, ay in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd))]
            zz = max(g(px, py) for px, py in pts) + 0.008
            m.slab(pts, zz, col, mat=WATER if col == PAL["paddy_water"] else 0, thick=0.2)


def terraces(m, g, cx, cy, r=0.9, levels=7, seed=0, hstep=0.05):
    """A hill carved into rice terraces: stacked irregular rings, alternately flooded and green."""
    rnd = random.Random(seed)
    base = min(g(cx + r * cos(a), cy + r * sin(a)) for a in [k * pi / 6 for k in range(12)])
    n = 40
    phase = [rnd.random() * 6 for _ in range(4)]
    for L in range(levels):
        t = L / levels
        rr = r * (1 - 0.82 * t)
        ring = []
        for k in range(n):
            a = 2 * pi * k / n
            wob = 1 + 0.16 * sin(3 * a + phase[0]) + 0.08 * sin(5 * a + phase[1] + L * 0.4) + 0.05 * sin(9 * a + phase[2])
            ring.append((cx + cos(a) * rr * wob, cy + sin(a) * rr * wob * 0.85))
        z = base + (L + 1) * hstep
        col = PAL["paddy_water"] if L % 2 == 0 else PAL["paddy"]
        m.slab(ring, z, col, mat=WATER if L % 2 == 0 else 0, thick=hstep + (0.3 if L == 0 else 0.0))
        # green lip along each terrace edge
        for k in range(n):
            (xa, ya), (xb, yb) = ring[k], ring[(k + 1) % n]
            m.box((xa + xb) / 2, (ya + yb) / 2, z, hypot(xb - xa, yb - ya), 0.012, 0.01, PAL["bund"], atan2(yb - ya, xb - xa))
    return base + levels * hstep


# ------------------------------------------------------------------------------------------ ships & travellers
def _hull(m, x, y, heading, L, B, D, color, z=SEA, sheer=0.35, stern_h=0.5):
    """Junk-style hull: flat transom stern, raised bow and stern, keel below the waterline."""
    xs = [-0.5, -0.35, -0.1, 0.15, 0.38, 0.5]
    wid = [0.62, 0.95, 1.0, 0.95, 0.7, 0.35]
    top = [stern_h, 0.18, 0.0, 0.02, 0.12, sheer]
    verts, faces, cols = [], [], []
    for i, (u, wf, tf) in enumerate(zip(xs, wid, top)):
        bw = B * wf / 2
        verts += [(u * L, -bw, D * (0.35 + tf)), (u * L, bw, D * (0.35 + tf)), (u * L, bw * 0.55, -D * 0.6), (u * L, -bw * 0.55, -D * 0.6)]
    n = len(xs)
    for i in range(n - 1):
        a, b = i * 4, (i + 1) * 4
        faces += [[a, b, b + 3, a + 3], [a + 1, a + 2, b + 2, b + 1], [a + 3, b + 3, b + 2, a + 2], [a, a + 1, b + 1, b]]
        cols += [shade(color, 0.9), shade(color, 1.0), shade(color, 0.7), PAL["wood_light"]]
    faces += [[0, 3, 2, 1], [(n - 1) * 4, (n - 1) * 4 + 1, (n - 1) * 4 + 2, (n - 1) * 4 + 3]]
    cols += [shade(color, 0.85), shade(color, 0.85)]
    Mt = m.M(x, y, z, heading)
    m.mesh(verts, faces, color, Mt, 0, cols)
    return Mt


def _lug_sail(m, Mt, u, height, width, color, z0, battens=5, rake=0.0):
    """Battened lug sail on a mast at hull position u (fraction of length), in the hull's frame."""
    m.box(u, 0, z0, width * 0.04, width * 0.04, height * 1.12, PAL["wood_dark"], M=Mt)
    verts = [(u - width * 0.62, 0.0, z0 + height * 0.18), (u + width * 0.38, 0.0, z0 + height * 0.12),
             (u + width * 0.46 + rake, 0.0, z0 + height), (u - width * 0.5 + rake, 0.0, z0 + height * 1.05)]
    m.mesh(verts, [[0, 1, 2, 3]], color, Mt)
    for k in range(1, battens):
        t = k / battens
        za = z0 + height * (0.18 + 0.87 * t)
        m.box(u - width * 0.07 + rake * t, 0.0, za, width * 1.02, width * 0.022, width * 0.018, shade(color, 0.72), M=Mt)


def junk(m, x, y, heading, L=0.5, masts=3, sail="sail_mat", hull="hull", z=SEA):
    B, D = L * 0.3, L * 0.14
    Mt = _hull(m, x, y, heading, L, B, D, P(hull), z)
    m.box(-0.38 * L, 0, D * 0.6, L * 0.2, B * 0.7, D * 0.8, P("wood"), M=Mt)  # stern castle
    spots = {1: [0.05], 2: [-0.1, 0.22], 3: [-0.2, 0.05, 0.3], 4: [-0.28, -0.05, 0.16, 0.36], 5: [-0.3, -0.12, 0.06, 0.22, 0.38]}[masts]
    for i, u in enumerate(spots):
        hgt = L * (0.7 if i == len(spots) // 2 else 0.52)
        _lug_sail(m, Mt, u * L, hgt, L * 0.24, P(sail), D * 0.5)


def treasure_ship(m, x, y, heading, L=0.9, z=SEA):
    """Zheng He's baochuan: long, beamy, many masts, a tall stern castle."""
    B, D = L * 0.36, L * 0.13
    Mt = _hull(m, x, y, heading, L, B, D, P("hull_red"), z, sheer=0.45, stern_h=0.9)
    m.box(-0.36 * L, 0, D * 0.8, L * 0.24, B * 0.78, D * 1.2, P("red"), M=Mt)
    m.roof(-0.36 * L, 0, D * 2.0, L * 0.2, B * 0.62, D * 0.7, P("roof"), 0.0, over=0.02, M=Mt)
    for i, u in enumerate([-0.18, -0.06, 0.06, 0.18, 0.3, 0.4]):
        hgt = L * (0.62 if i in (2, 3) else 0.46)
        _lug_sail(m, Mt, u * L, hgt, L * 0.16, P("sail"), D * 0.6)


def dhow(m, x, y, heading, L=0.35, z=SEA):
    B, D = L * 0.24, L * 0.12
    Mt = _hull(m, x, y, heading, L, B, D, P("wood"), z, sheer=0.55, stern_h=0.45)
    m.box(0.05 * L, 0, D * 0.4, L * 0.03, L * 0.03, L * 0.75, P("wood_dark"), M=Mt)
    m.mesh([(-0.35 * L, 0, D * 0.9), (0.45 * L, 0, L * 0.95), (0.05 * L, 0, L * 0.25)], [[0, 1, 2]], P("sail_white"), Mt)


def barge(m, x, y, heading, L=0.3, z=SEA):
    B, D = L * 0.3, L * 0.1
    Mt = _hull(m, x, y, heading, L, B, D, P("wood"), z, sheer=0.15, stern_h=0.2)
    m.box(-0.1 * L, 0, D * 0.4, L * 0.45, B * 0.8, D * 1.2, P("roof_thatch"), M=Mt, taper=0.7)
    _lug_sail(m, Mt, 0.2 * L, L * 0.55, L * 0.22, P("sail_mat"), D * 0.4, battens=4)


def sampan(m, x, y, heading, L=0.12, z=SEA):
    B, D = L * 0.28, L * 0.1
    Mt = _hull(m, x, y, heading, L, B, D, P("wood"), z, sheer=0.2, stern_h=0.2)
    m.box(-0.05 * L, 0, D * 0.35, L * 0.4, B * 0.9, D * 1.2, P("roof_thatch"), M=Mt, taper=0.6)


def camel(m, x, y, z, heading, s=0.06, color="dirt", pack="felt_trim"):
    Mt = m.M(x, y, z, heading)
    c = P(color)
    for lx, ly in ((-0.3, -0.12), (-0.3, 0.12), (0.3, -0.12), (0.3, 0.12)):
        m.box(lx * s, ly * s, 0, s * 0.1, s * 0.1, s * 0.75, shade(c, 0.85), M=Mt)
    m.box(0, 0, s * 0.72, s * 0.95, s * 0.42, s * 0.36, c, M=Mt)
    m.sphere(0, 0, s * 0.95, s * 0.2, shade(c, 1.05), n=6, rings=3, M=Mt)
    m.box(0, 0, s * 1.05, s * 0.5, s * 0.5, s * 0.18, P(pack), M=Mt)
    m.box(s * 0.55, 0, s * 0.85, s * 0.14, s * 0.12, s * 0.5, c, M=Mt, rot=0.0)
    m.box(s * 0.68, 0, s * 1.25, s * 0.26, s * 0.13, s * 0.12, shade(c, 1.05), M=Mt)


def ger(m, g, x, y, r=0.05, color="felt"):
    z, _ = footprint_z(g, x, y, r * 2, r * 2)
    m.prism(x, y, z - 0.2, r, 0.2 + r * 0.7, 10, P(color))
    m.prism(x, y, z + r * 0.7, r * 1.02, r * 0.45, 10, shade(P(color), 0.95), r * 0.18)
    m.prism(x, y, z + r * 0.35, r * 1.005, r * 0.08, 10, P("felt_trim"), r * 1.005, cap=False)


# ------------------------------------------------------------------------------------------ industry
def smoke(m, x, y, z, h=0.6, s=0.08, seed=0, color="smoke"):
    rnd = random.Random(seed)
    for k in range(6):
        t = k / 5
        m.sphere(x + t * h * 0.35 + rnd.uniform(-0.02, 0.02), y + t * h * 0.15, z + t * h, s * (0.6 + 1.1 * t), shade(P(color), 1.0 - 0.08 * t),
                 n=7, rings=4, jitter=0.15, seed=seed + k)


def kiln(m, g, x0, y0, x1, y1, w=0.08, seed=0):
    """Dragon kiln: a long brick tunnel climbing a slope in stepped chambers, a stack at the top."""
    L = hypot(x1 - x0, y1 - y0)
    a = atan2(y1 - y0, x1 - x0)
    n = max(4, int(L / (w * 0.9)))
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        xa, ya = x0 + (x1 - x0) * (t0 + t1) / 2, y0 + (y1 - y0) * (t0 + t1) / 2
        z = g(xa, ya)
        seg = L / n * 1.02
        m.box(xa, ya, z - 0.2, seg, w, 0.2 + w * 0.35, P("brick"), a, top=shade(P("brick"), 1.05))
        m.lathe(xa, ya, z + w * 0.35, [(w * 0.5, 0), (w * 0.45, w * 0.18), (w * 0.28, w * 0.34), (0.001, w * 0.4)], 8, shade(P("brick"), 0.95))
    z1 = g(x1, y1)
    m.prism(x1, y1, z1, w * 0.3, w * 2.2, 8, P("brick"), w * 0.22)
    smoke(m, x1, y1, z1 + w * 2.2, h=0.45, s=0.05, seed=seed)
    # stacks of fired wares at the kiln mouth
    zb = g(x0, y0)
    for k in range(4):
        m.prism(x0 - 0.06 * cos(a) + 0.04 * (k - 1.5) * sin(a), y0 - 0.06 * sin(a) - 0.04 * (k - 1.5) * cos(a), zb, 0.014, 0.03, 8,
                P("white") if k % 2 else P("cobalt"), 0.012)


def furnace(m, g, x, y, s=0.12, seed=0):
    """Blast furnace: a tapered stone stack, glowing mouth, a bellows shed and a smoke plume."""
    z, _ = footprint_z(g, x, y, s * 1.4, s * 1.4)
    m.prism(x, y, z - 0.2, s * 0.6, 0.2 + s * 1.5, 8, P("stone_dark"), s * 0.38)
    m.prism(x, y, z + s * 1.5, s * 0.3, s * 0.06, 8, P("fire"), s * 0.28, mat=GLOW)
    m.box(x + s * 0.62, y, z, s * 0.12, s * 0.2, s * 0.12, P("fire"), mat=GLOW)
    house(m, g, x + s * 1.1, y + s * 0.2, s * 0.9, s * 0.6, 0.0, "wood", "roof_thatch")
    smoke(m, x, y, z + s * 1.6, h=0.7, s=0.06, seed=seed, color="smoke")


# ------------------------------------------------------------------------------------------ special buildings
def kinkaku(m, g, x, y, s=0.3, rot=0.0, z=None):
    """The Golden Pavilion: a natural-wood first storey, two gilded upper storeys, shingle roofs, a phoenix on top."""
    z = g(x, y) if z is None else z
    Mt = m.M(x, y, z, rot)
    m.box(0, 0, -0.25, s * 1.2, s * 0.95, 0.25 + s * 0.06, P("stone"), M=Mt)
    m.box(0, 0, s * 0.06, s * 1.05, s * 0.8, s * 0.36, P("wood_light"), M=Mt)
    m.box(0, 0, s * 0.12, s * 1.06, s * 0.81, s * 0.2, P("white"), M=Mt)
    m.roof(0, 0, s * 0.42, s * 1.1, s * 0.85, s * 0.12, P("roof_brown"), 0.0, over=s * 0.1, lift=s * 0.03, M=Mt, ridge_color=False)
    m.box(0, 0, s * 0.5, s * 0.95, s * 0.72, s * 0.32, P("gold"), mat=GOLD, M=Mt)
    m.roof(0, 0, s * 0.82, s * 1.0, s * 0.78, s * 0.1, P("roof_brown"), 0.0, over=s * 0.1, lift=s * 0.03, M=Mt, ridge_color=False)
    m.box(0, 0, s * 0.9, s * 0.62, s * 0.62, s * 0.3, P("gold"), mat=GOLD, M=Mt)
    m.roof(0, 0, s * 1.2, s * 0.66, s * 0.66, s * 0.3, P("roof_brown"), 0.0, over=s * 0.12, lift=s * 0.06, M=Mt)
    m.prism(0, 0, s * 1.48, s * 0.03, s * 0.12, 6, P("gold"), s * 0.005, mat=GOLD, M=Mt)
    m.box(s * 0.62, 0, s * 0.06, s * 0.25, s * 0.35, s * 0.2, P("wood_light"), M=Mt)  # the fishing deck


def buddha(m, g, x, y, s=0.4, rot=0.0):
    """Kamakura's seated bronze Great Buddha (1252)."""
    z, _ = footprint_z(g, x, y, s, s)
    Mt = m.M(x, y, z, rot)
    c = P("bronze")
    m.box(0, 0, -0.2, s * 1.1, s * 0.9, 0.2 + s * 0.12, P("stone"), M=Mt)
    m.lathe(0, 0, s * 0.12, [(s * 0.45, 0), (s * 0.44, s * 0.14), (s * 0.3, s * 0.22), (s * 0.001, s * 0.24)], 12, c, M=Mt)
    m.lathe(0, 0, s * 0.3, [(s * 0.26, 0), (s * 0.28, s * 0.25), (s * 0.2, s * 0.5), (s * 0.08, s * 0.56)], 12, c, M=Mt)
    m.sphere(0, 0, s * 0.82, s * 0.14, shade(c, 1.05), n=10, rings=6, sz=1.1, M=Mt)
    m.sphere(0, 0, s * 1.08, s * 0.08, shade(c, 0.95), n=8, rings=4, M=Mt)


def dome(m, x, y, z, r, color="turquoise", drum=0.5, point=True):
    prof = [(r * 1.02, 0), (r * 1.02, r * drum)]
    for k in range(1, 8):
        t = k / 8
        prof.append((r * 1.05 * math.cos(t * pi / 2) ** 0.8, r * drum + r * 1.15 * math.sin(t * pi / 2)))
    if point:
        prof.append((0.001, r * drum + r * 1.45))
    m.lathe(x, y, z, prof, 16, P(color))


def minaret(m, x, y, z, r, h, color="brick", cap="turquoise"):
    m.prism(x, y, z - 0.2, r, h + 0.2, 10, P(color), r * 0.8)
    m.prism(x, y, z + h * 0.82, r * 1.25, r * 0.4, 10, shade(P(color), 1.1), r * 1.25)
    m.prism(x, y, z + h, r * 0.8, r * 1.6, 10, P(cap), 0.002)


def cham_tower(m, g, x, y, s=0.2):
    """Cham brick temple tower: a tall square cella and stepped, shrinking upper tiers."""
    z, _ = footprint_z(g, x, y, s, s)
    c = P("cham")
    m.box(x, y, z - 0.2, s * 1.2, s * 1.2, 0.2 + s * 0.12, P("stone"))
    m.box(x, y, z + s * 0.12, s * 0.8, s * 0.8, s * 1.0, c)
    m.box(x + s * 0.46, y, z + s * 0.12, s * 0.2, s * 0.34, s * 0.6, shade(c, 0.9))
    zz = z + s * 1.12
    for k in range(3):
        f = 0.72 - 0.16 * k
        m.box(x, y, zz, s * f, s * f, s * 0.26, shade(c, 1.0 - 0.05 * k), taper=0.9)
        zz += s * 0.26
    m.prism(x, y, zz, s * 0.12, s * 0.3, 8, shade(c, 0.9), 0.002)


def gnomon_tower(m, g, x, y, s=0.3):
    """Guo Shoujing-style observatory tower with a long stone measuring scale running north."""
    z, _ = footprint_z(g, x, y, s, s)
    m.box(x, y, z - 0.2, s, s, 0.2 + s * 0.8, P("brick_grey"), taper=0.72)
    m.box(x, y, z + s * 0.8, s * 0.26, s * 0.72, s * 0.28, P("brick_grey"))
    m.box(x, y + s * 1.7, z, s * 0.12, s * 2.6, s * 0.05, P("stone_light"))


def armillary(m, x, y, z, r=0.08, color="bronze"):
    for k in range(3):
        rot = [0, pi / 2, pi / 4][k]
        for i in range(16):
            a0, a1 = 2 * pi * i / 16, 2 * pi * (i + 1) / 16
            if k == 0:
                p0, p1 = (r * cos(a0), r * sin(a0), 0), (r * cos(a1), r * sin(a1), 0)
            else:
                p0 = (r * cos(a0) * cos(rot), r * cos(a0) * sin(rot), r * sin(a0))
                p1 = (r * cos(a1) * cos(rot), r * cos(a1) * sin(rot), r * sin(a1))
            mx, my, mz = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2
            m.box(x + mx, y + my, z + r + mz - 0.004, r * 0.42, 0.008, 0.008, P(color), atan2(p1[1] - p0[1], p1[0] - p0[0]))
    m.prism(x, y, z, r * 0.3, r * 0.9, 6, P("stone"), r * 0.2)


# ------------------------------------------------------------------------------------------ more parts
def torii(m, g, x, y, s=0.12, rot=0.0, color="red"):
    z = g(x, y)
    c, sn = cos(rot), sin(rot)
    for side in (-1, 1):
        m.prism(x + c * side * s * 0.4, y + sn * side * s * 0.4, z - 0.1, s * 0.05, 0.1 + s, 8, P(color), s * 0.045)
    m.box(x, y, z + s * 0.78, s * 1.0, s * 0.07, s * 0.06, P(color), rot)
    m.box(x, y, z + s * 0.95, s * 1.25, s * 0.09, s * 0.07, P("black"), rot, taper=1.0)


def tent(m, g, x, y, s=0.06, rot=0.0, color="white", stripe="black"):
    z = g(x, y)
    m.box(x, y, z - 0.1, s * 1.2, s * 0.8, 0.1 + s * 0.45, P(color), rot)
    m.box(x, y, z + s * 0.2, s * 1.21, s * 0.81, s * 0.12, P(stripe), rot)


def stake(m, x, y, z0, h=0.12, r=0.012, lean=0.0, color="wood_dark"):
    m.prism(x, y, z0 - 0.1, r, 0.1 + h, 5, P(color), 0.001, rot=lean)


def pile(m, g, x, y, r, h, color):
    z = g(x, y)
    m.lathe(x, y, z - 0.03, [(r, 0), (r * 0.7, h * 0.5), (0.001, h)], 9, P(color))


def waterwheel(m, x, y, z, r=0.06, rot=0.0):
    c, sn = cos(rot), sin(rot)
    for k in range(8):
        a = k * pi / 4
        px, pz = cos(a) * r * 0.55, sin(a) * r * 0.55
        m.box(x + c * 0.0 - sn * px, y + sn * 0.0 + c * px, z + r + pz - 0.004, 0.015, r * 0.9, 0.008, P("wood"), rot + pi / 2)
    m.prism(x, y, z + r - 0.01, 0.008, 0.02, 6, P("wood_dark"), 0.008)


def one_pillar(m, g, x, y, s=0.1):
    """Hanoi's One Pillar Pagoda: a small shrine on a single column rising from a lotus pond."""
    z = g(x, y)
    m.slab([(x - s, y - s), (x + s, y - s), (x + s, y + s), (x - s, y + s)], z + 0.01, P("pond"), mat=WATER, thick=0.2)
    m.prism(x, y, z, s * 0.12, s * 0.7, 8, P("stone"), s * 0.12)
    m.box(x, y, z + s * 0.7, s * 0.55, s * 0.55, s * 0.28, P("wood"))
    m.roof(x, y, z + s * 0.98, s * 0.6, s * 0.6, s * 0.3, P("roof_dark"), over=s * 0.12, lift=s * 0.1)


def striped_wall(m, g, pts, h=0.1, t=0.06, base="stone_dark", stripes=("red", "white")):
    """Sakya-style monastery walls: dark grey with vertical red and white bands."""
    wall(m, g, pts, h=h, t=t, color=base)
    n = len(pts)
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        L = hypot(x1 - x0, y1 - y0)
        k = max(2, int(L / 0.12))
        a = atan2(y1 - y0, x1 - x0)
        for j in range(1, k):
            t_ = j / k
            x, y = x0 + (x1 - x0) * t_, y0 + (y1 - y0) * t_
            z = g(x, y)
            m.box(x, y, z + h * 0.1, 0.018, t * 1.08, h * 0.95, P(stripes[j % 2]), a)
