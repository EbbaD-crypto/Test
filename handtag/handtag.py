"""Två lekfulla garderobshandtag i quirky skandinavisk inredningsanda
(mönsterglädje, mjuka organiska former, pärlor och snirklar).

  snirkel  – greppbygel, 128 mm c/c, där bygeln slingrar sig i sidled som ett
             band och sväller i pärlor, med stora kulor i ändarna.
  marang   – knopp som en vriden maräng/pumpa på en musslad rosett, med en
             liten pärla på toppen.
  marshmallow – knopp: en puffig, lite ojämn marshmallow på en kort hals.
  spett    – greppbygel, 128 mm c/c: tre marshmallows på ett grillspett.

Båda har M4-hål (3,4 mm förborrning för gänga, 12 mm djupt) i fötterna, så de
skruvas fast inifrån dörren med vanliga möbelskruvar M4.

    python3 handtag.py            # snirkel/marang/marshmallow/spett.stl i samma mapp
"""
import os
import numpy as np
import trimesh
import manifold3d as mf
from scipy.interpolate import PchipInterpolator

MAPP = os.path.dirname(os.path.abspath(__file__))
SEG = 64                 # segment per varv för kulor och cylindrar
HAL_D, HAL_DJUP = 3.4, 12.0


def till_manifold(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                               tri_verts=np.asarray(m.faces, np.uint32)))


def till_trimesh(m):
    g = m.to_mesh()
    return trimesh.Trimesh(g.vert_properties[:, :3], g.tri_verts, process=True)


def kula(p, r):
    return mf.Manifold.sphere(r, SEG).translate(tuple(p))


def hal(x=0.0, y=0.0):
    """Skruvhål underifrån."""
    return mf.Manifold.cylinder(HAL_DJUP + 0.01, HAL_D / 2, HAL_D / 2, 32).translate((x, y, -0.01))


def svarv(z, r, lober=None, n=192, form=None):
    """Rotationskropp ur profilen (z, r), med valfri lobning:
    lober(z) -> (antal, amplitud (andel av r), vridning i radianer),
    eller fri form: form(vinklar, z) -> multiplikator för radien."""
    v = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ringar = []
    for zi, ri in zip(z, r):
        if form:
            rr = ri * form(v, zi)
        elif lober:
            k, a, vr = lober(zi)
            rr = ri * (1 + a * np.cos(k * (v - vr)))
        else:
            rr = np.full(n, ri)
        ringar.append(np.column_stack([rr * np.cos(v), rr * np.sin(v), np.full(n, zi)]))
    pk = np.vstack(ringar + [[0, 0, z[0]], [0, 0, z[-1]]])
    ner, upp = len(pk) - 2, len(pk) - 1
    f = []
    for i in range(len(z) - 1):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n
            c, d = a + n, b + n
            f += [[a, b, d], [a, d, c]]
    for j in range(n):
        f.append([ner, (j + 1) % n, j])
        s = (len(z) - 1) * n
        f.append([upp, s + j, s + (j + 1) % n])
    m = trimesh.Trimesh(pk, np.array(f), process=True)
    m.fix_normals()
    return till_manifold(m)


def mjuk_profil(punkter, n=160):
    z, r = np.array(punkter, float).T
    t = np.r_[0, np.cumsum(np.hypot(np.diff(z), np.diff(r)))]
    tt = np.linspace(0, t[-1], n)
    return PchipInterpolator(t, z)(tt), PchipInterpolator(t, r)(tt)


# --- Snirkel -----------------------------------------------------------------
CC = 128.0               # hålavstånd
HOJD = 30.0              # bygelns mitt över dörren
VAG = 7.0                # hur mycket bygeln slingrar i sidled
UTSTICK = 18.0           # hur långt bygeln fortsätter förbi stolparna


def snirkel():
    x = np.linspace(-CC / 2 - UTSTICK, CC / 2 + UTSTICK, 181)
    y = VAG * np.sin(2 * np.pi * x / CC * 2)              # två hela vågor, noll vid stolparna
    r = 5.6 + 1.3 * np.cos(2 * np.pi * x / (CC / 4)) ** 2  # pärlor: tjockt vid stolpar och mellan dem
    p = np.column_stack([x, y, np.full_like(x, HOJD)])
    delar = [mf.Manifold.batch_hull([kula(p[i], r[i]), kula(p[i + 1], r[i + 1])])
             for i in range(len(x) - 1)]
    for s in (-1, 1):
        delar.append(kula((s * (CC / 2 + UTSTICK), 0, HOJD), 10.5))
    # stolpar: utsvängd fot mot dörren, smal hals upp mot bygeln
    z, rp = mjuk_profil([(0, 0), (0, 9.5), (1.2, 9.6), (3, 8.0), (8, 5.6), (16, 4.6), (HOJD, 5.2), (HOJD, 0)])
    stolpe = svarv(z, rp, lober=lambda zi: (10, 0.06 * np.clip(1 - zi / 4, 0, 1), 0.0))
    for s in (-1, 1):
        delar.append(stolpe.translate((s * CC / 2, 0, 0)))
    m = mf.Manifold.batch_boolean(delar, mf.OpType.Add)
    for s in (-1, 1):
        m = m - hal(s * CC / 2)
    return m


# --- Maräng ------------------------------------------------------------------
def marang():
    z, r = mjuk_profil([(0, 0), (0, 15.5), (1.6, 16.5), (3.2, 15.5), (5, 11), (8, 6.2), (13, 5.4),
                        (16, 8), (19, 13.5), (23, 17), (27, 17.2), (31, 14.5), (34.5, 9.5),
                        (36.8, 4.5), (37.6, 0)], n=220)

    def lober(zi):
        if zi < 6:                                   # musslad rosett
            return 12, 0.07 * np.clip((6 - zi) / 3, 0, 1), 0.0
        a = 0.11 * np.clip((zi - 14) / 5, 0, 1)      # vriden maräng
        return 8, a, 0.9 * (zi - 14) / 24

    m = svarv(z, r, lober=lober) + kula((0, 0, 39.2), 3.8)
    return m - hal()


# --- Marshmallow -------------------------------------------------------------
def mallow_profil(z0, hojd, r, n=5.0, kudde=0.9, puff=0.5):
    """Puffig cylinder: superellips (n styr hur fyrkantig), kuddiga ändar
    (kudde mm) och lätt utbuktande sidor (puff mm)."""
    f = np.linspace(-np.pi / 2, np.pi / 2, 240)
    c, s_ = np.cos(f), np.sin(f)
    x = r * np.abs(c) ** (2 / n)
    y = hojd / 2 * np.sign(s_) * np.abs(s_) ** (2 / n)
    y += np.sign(s_) * kudde * np.clip(1 - (x / r) ** 2, 0, 1) * np.abs(s_) ** 2
    x += puff * np.clip(1 - (2 * y / hojd) ** 2, 0, 1)
    x[0] = x[-1] = 0
    return z0 + hojd / 2 + y, x


def klumpig(fro, z0, hojd):
    """Lite ojämn, handgjord form – varje marshmallow sin egen."""
    g = np.random.default_rng(fro)
    f = g.uniform(0, 2 * np.pi, 4)

    def form(v, zi):
        t = (zi - z0) / hojd
        return (1 + 0.022 * np.sin(2 * v + f[0] + 0.8 * t) + 0.014 * np.sin(3 * v + f[1])
                + 0.008 * np.sin(5 * v + f[2] + 2 * t) + 0.01 * np.sin(np.pi * t + f[3]) * np.cos(v))
    return form


def marshmallow():
    """Knopp: en marshmallow på högkant på en kort hals, svarvad i ett stycke."""
    z0, h = 8.0, 25.0
    zm, rm = mallow_profil(z0, h, 16.5)
    hals = 5.5
    i = np.argmax(rm > hals + 0.6)                       # där marshmallowens undersida passerar halsen
    zf, rf = mjuk_profil([(0, 0), (0, 11), (1.5, 11), (3.5, 7.5), (5.5, hals), (zm[i] - 1.0, hals)])
    z, r = np.r_[zf, zm[i:]], np.r_[rf, rm[i:]]
    lump = klumpig(3, z0, h)
    return svarv(z, r, form=lambda v, zi: 1 + (lump(v, zi) - 1) * np.clip((zi - z0 + 1) / 3, 0, 1)) - hal()


SPETT_HOJD = 36.0        # spettets mitt över dörren (ger ca 23 mm fingerplats under)


def spett():
    """Greppbygel, 128 mm c/c: tre marshmallows uppträdda på ett grillspett."""
    delar = []
    for i, x in enumerate((-38.0, 0.0, 38.0)):
        z, r = mallow_profil(-14.0, 28.0, 13.5)
        m = svarv(z, r, form=klumpig(10 + i, -14.0, 28.0))
        delar.append(m.rotate((0, 90, 0)).rotate((90 * i + 20, 0, 0)).translate((x, 0, SPETT_HOJD)))
    langd = CC + 24
    pinne = mf.Manifold.cylinder(langd, 3.2, 3.2, 48, center=True).rotate((0, 90, 0))
    delar.append(pinne.translate((0, 0, SPETT_HOJD)))
    for s in (-1, 1):
        delar.append(kula((s * langd / 2, 0, SPETT_HOJD), 4.2))
    z, rp = mjuk_profil([(0, 0), (0, 9.5), (1.2, 9.6), (3, 8.0), (8, 5.6), (20, 4.6), (SPETT_HOJD, 5.0), (SPETT_HOJD, 0)])
    stolpe = svarv(z, rp)
    for s in (-1, 1):
        delar.append(stolpe.translate((s * CC / 2, 0, 0)))
    m = mf.Manifold.batch_boolean(delar, mf.OpType.Add)
    for s in (-1, 1):
        m = m - hal(s * CC / 2)
    return m


def main():
    for namn, f in (("snirkel", snirkel), ("marang", marang), ("marshmallow", marshmallow), ("spett", spett)):
        m = till_trimesh(f())
        assert m.is_watertight, namn
        m.export(os.path.join(MAPP, f"{namn}.stl"))
        dx, dy, dz = m.extents
        print(f"{namn}.stl: {dx:.0f} x {dy:.0f} x {dz:.0f} mm, {len(m.faces)} trianglar, {m.volume / 1000:.1f} cm³")


if __name__ == "__main__":
    main()
