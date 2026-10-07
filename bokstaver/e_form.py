"""Nytt e byggt av en mittlinje med jämn linjetjocklek: ögat är en ellips med
samma lutning och proportion som hålet i a, nedre svängen en Bezierkurva."""
import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

def bez(P, n=80):
    P = np.asarray(P, float); t = np.linspace(0, 1, n)[:, None]
    return ((1-t)**3)*P[0] + 3*((1-t)**2)*t*P[1] + 3*(1-t)*t*t*P[2] + t**3*P[3]

def e_poly(oga=(0.26, 0.16), W=0.50, vinkel=56, cx=0.98, svans=(1.5, 0.34), lut=0.18, h=2.0):
    a, b = oga[0] + W/2, oga[1] + W/2
    v = np.radians(vinkel); R = np.array([[np.cos(v), -np.sin(v)], [np.sin(v), np.cos(v)]])
    halv = np.sqrt((a*np.sin(v))**2 + (b*np.cos(v))**2)
    c = np.array([cx, h - W/2 - halv])
    t = np.linspace(0, 2*np.pi, 400)
    E = (R @ np.vstack([a*np.cos(t), b*np.sin(t)])).T + c
    i = E[:, 0].argmin(); P0 = E[i]
    yb = W/2
    xb = P0[0] + 0.45 - lut                 # bottenpunkt (lutning: svängen går in åt vänster nedtill)
    nedre = bez([P0, P0 + [-lut*0.6, -0.5], [xb - 0.35, yb], [xb, yb]])
    svng = bez([[xb, yb], [xb + 0.35, yb], [svans[0] - 0.12, svans[1] - 0.12], svans])
    g = unary_union([LineString(E).buffer(W/2, 48), LineString(nedre).buffer(W/2, 48), LineString(svng).buffer(W/2, 48)])
    oga_poly = Polygon((R @ np.vstack([oga[0]*np.cos(t), oga[1]*np.sin(t)])).T + c)
    return g.difference(oga_poly).buffer(0.03).buffer(-0.03)

def oppning(g):
    """Minsta glipan mellan ögats bågen och svansen (vid högersidan)."""
    from shapely.geometry import box
    hal = box(-1, -1, 3, 3).difference(g)
    return hal
