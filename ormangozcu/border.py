"""Türkiye land border for keeping only detections inside the country.

The FIRMS area query returns a rectangle that also covers parts of Greece, Bulgaria,
Georgia, Armenia, Iran, Iraq, Syria and Cyprus. The border is Natural Earth 10 m
Admin-0 (public domain), outer rings only, rounded to 0.001 degrees.
"""
import json
from functools import lru_cache
from pathlib import Path

BORDER_FILE = Path(__file__).with_name("turkiye_border.json")


@lru_cache(maxsize=1)
def _polygons():
    data = json.loads(BORDER_FILE.read_text(encoding="utf-8"))
    out = []
    for ring in data["polygons"]:
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        out.append((ring, (min(xs), min(ys), max(xs), max(ys))))
    return out


def _in_ring(lon, lat, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def in_turkiye(lat, lon):
    for ring, (x0, y0, x1, y1) in _polygons():
        if x0 <= lon <= x1 and y0 <= lat <= y1 and _in_ring(lon, lat, ring):
            return True
    return False
