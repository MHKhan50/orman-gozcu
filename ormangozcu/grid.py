"""0.5-degree grid over Türkiye and the three longitude regions used for transfer tests."""
import math

CELL = 0.5
BBOX = (25.5, 35.5, 45.0, 42.5)  # west, south, east, north
REGIONS = (("west", -180.0, 30.0), ("central", 30.0, 36.0), ("east", 36.0, 180.0))


def cell_of(lat, lon):
    """Cell id 'r{row}_c{col}' for a point; rows count north from the bbox south edge."""
    row = int(math.floor((lat - BBOX[1]) / CELL))
    col = int(math.floor((lon - BBOX[0]) / CELL))
    return "r%d_c%d" % (row, col)


def parse(cell):
    r, c = cell.split("_")
    return int(r[1:]), int(c[1:])


def centre(cell):
    row, col = parse(cell)
    return BBOX[1] + (row + 0.5) * CELL, BBOX[0] + (col + 0.5) * CELL


def neighbours(cell):
    row, col = parse(cell)
    return ["r%d_c%d" % (row + dr, col + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc]


def weather_block(cell):
    """1-degree block (2 x 2 fire cells) whose centre is used for weather, to keep API calls low."""
    row, col = parse(cell)
    return "b%d_%d" % (row // 2, col // 2)


def block_centre(block):
    r, c = (int(x) for x in block[1:].split("_"))
    return BBOX[1] + (r + 0.5) * 2 * CELL, BBOX[0] + (c + 0.5) * 2 * CELL


def region(cell):
    lon = centre(cell)[1]
    for name, lo, hi in REGIONS:
        if lo <= lon < hi:
            return name
    raise ValueError(cell)
