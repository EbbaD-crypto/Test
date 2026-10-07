"""e som ett enda drag med jämn tjocklek: tvärstrecket snett uppåt höger,
upp och runt, ner längs vänstersidan, runt botten och ut i svansen."""
import numpy as np
from scipy.interpolate import splprep, splev
from shapely.geometry import LineString

def e_drag(punkter, W=0.5, s=0.002):
    P = np.array(punkter, float)
    tck, _ = splprep(P.T, s=s, k=3)
    x, y = splev(np.linspace(0, 1, 600), tck)
    linje = np.column_stack([x, y])
    return LineString(linje).buffer(W / 2, 48), linje

STANDARD = [(0.50, 0.90), (0.95, 1.13), (1.36, 1.36), (1.40, 1.58), (1.05, 1.75), (0.62, 1.66),
            (0.33, 1.25), (0.30, 0.75), (0.52, 0.33), (0.95, 0.25), (1.30, 0.32), (1.45, 0.48)]

G = [(0.45, 0.80), (0.80, 0.90), (1.18, 1.08), (1.45, 1.33), (1.46, 1.62), (1.06, 1.77), (0.60, 1.67),
     (0.30, 1.28), (0.27, 0.80), (0.46, 0.32), (0.90, 0.23), (1.28, 0.26), (1.52, 0.36)]


def nytt_e(W=0.47, runda=0.1):
    g, _ = e_drag(G, W=W, s=0.004)
    g = g.buffer(runda).buffer(-runda)          # rundar spetsiga hörn i ögat och öppningen
    import numpy as np
    from shapely import affinity
    g = affinity.translate(g, -g.bounds[0], -max(g.bounds[1], -0.02))
    return [[np.array(q.exterior.coords)] + [np.array(i.coords) for i in q.interiors] for q in getattr(g, 'geoms', [g])], g.bounds[2]

# svansen uppåt (användaren testar): A lite, B som öglan. Använd runda=0.05.
G_A = G[:-3] + [(0.86, 0.23), (1.16, 0.28), (1.42, 0.44)]
G_B = G[:-3] + [(0.84, 0.23), (1.12, 0.30), (1.38, 0.50)]


def e_med_svans(slut=(1.42, 0.42), vinkel=27, W=0.47, runda=0.05, oga_runda=0.1):
    """Samma ögla som G (oförändrad), bara svansen efter bottenpunkten byts mot
    en kurva som slutar med given vinkel. Ögat kan rundas lite (oga_runda)."""
    import numpy as np
    from scipy.interpolate import splprep, splev
    from shapely.geometry import LineString, Polygon
    P = np.array(G, float)
    tck, _ = splprep(P.T, s=0.004, k=3)
    u = np.linspace(0, 1, 800)
    x, y = splev(u, tck); dx, dy = splev(u, tck, der=1)
    halv = len(u) // 2
    i = halv + np.argmin(y[halv:])                 # bottenpunkten
    P0 = np.array([x[i], y[i]]); d0 = np.array([dx[i], dy[i]]); d0 /= np.linalg.norm(d0)
    P3 = np.array(slut, float); v = np.radians(vinkel); d3 = np.array([np.cos(v), np.sin(v)])
    L = np.linalg.norm(P3 - P0)
    t = np.linspace(0, 1, 100)[:, None]
    B = ((1-t)**3)*P0 + 3*((1-t)**2)*t*(P0 + d0*L*0.35) + 3*(1-t)*t*t*(P3 - d3*L*0.2) + t**3*P3
    linje = np.vstack([np.column_stack([x[:i], y[:i]]), B])
    g = LineString(linje).buffer(W / 2, 48).buffer(runda).buffer(-runda)
    if oga_runda:
        ext = Polygon(g.exterior)
        hal = [Polygon(h).buffer(-oga_runda).buffer(oga_runda) for h in g.interiors]
        g = ext
        for h in hal:
            g = g.difference(h)
    return g


def e_nu_lyft(lyft=0.03, W=0.47, runda=0.1, oga_runda=0.0):
    """Nuvarande e (G) men svansens allra sista bit böjs väldigt lätt uppåt."""
    import numpy as np
    from scipy.interpolate import splprep, splev
    from shapely.geometry import LineString
    P = np.array(G, float)
    tck, _ = splprep(P.T, s=0.004, k=3)
    x, y = splev(np.linspace(0, 1, 800), tck)
    x, y = np.array(x), np.array(y)
    halv = len(x) // 2
    i = halv + np.argmin(y[halv:])
    s = np.clip((x - 1.25) / (x[-1] - 1.25), 0, 1)
    dy = np.where(np.arange(len(x)) > i, lyft * s ** 2.5, 0)
    g = LineString(np.column_stack([x, y + dy])).buffer(W / 2, 48)
    g = g.buffer(runda).buffer(-runda)
    if oga_runda:
        from shapely.geometry import Polygon
        hal = [Polygon(h).buffer(-oga_runda).buffer(oga_runda) for h in g.interiors]
        g = Polygon(g.exterior)
        for h in hal:
            g = g.difference(h)
    return g


def _ellipsbage(cx, cy, a, b, vinklar):
    import numpy as np
    K = np.tan(np.radians(10)); out = []
    for v in np.radians(vinklar):
        x, y = cx + a*np.cos(v), cy + b*np.sin(v); out.append((x + K*(y - cy), y))
    return out

# rundare ytterkant på öglan (V1 / V2)
G_V1 = G[:3] + _ellipsbage(0.86, 1.12, 0.60, 0.65, [20, 55, 90, 125, 160, 195]) + G[8:]
G_V2 = G[:3] + _ellipsbage(0.86, 1.10, 0.62, 0.67, [15, 50, 88, 125, 162, 198]) + G[8:]
