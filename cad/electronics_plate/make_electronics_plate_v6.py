"""Plexi plate v6 (2026-11-08): Raspberry Pi 4 + the CNC-milled Hexapod Rev4 PCB (100 x 80 mm, 4x M3 on 90 x 70).

The two boards do not fit side by side on the chassis plate, so they are STACKED:
  * the Pi 4 lies on the plate (4x M2.5 on 5-6 mm spacers), USB/LAN end towards +x;
  * the Rev4 PCB sits above it on 4x M3 x 30 mm spacers, centred on the plate.
    Its standoffs fall outside the Pi footprint; the Pi's ports stay reachable from the +x side.
Same outline, cable openings and chassis mounting slots as v2/v5. The four round chassis openings at
(+-48, +-33) are left solid because the Rev4 standoffs land there.

    .venv/bin/python cad/electronics_plate/make_electronics_plate_v6.py
    -> electronics_plate_v6.dxf / .svg / .lbrn2 / _preview.png beside this file
"""
import ezdxf
from shapely.geometry import Point
import make_electronics_plate as v2
import make_electronics_plate_v5 as v5

HERE = v2.HERE
PCB, PCB_C, PCB_PITCH, PCB_HOLE = (100., 80.), (0., 0.), (90., 70.), 3.2   # Rev4, M3
PI_C = (-4., -2.5)                                                          # found by a clearance search
STANDOFF_R, PI_SPACER_R = 3.5, 3.0


def pcb_points():
    return [(PCB_C[0]+sx*PCB_PITCH[0]/2, PCB_C[1]+sy*PCB_PITCH[1]/2) for sx in (-1, 1) for sy in (-1, 1)]


def pi_points():
    cx, cy = PI_C
    return [(x, cy+dy) for x in (cx-(v2.PI[0]/2-3.5), cx-(v2.PI[0]/2-61.5)) for dy in (-24.5, 24.5)]


def outlines():
    return [v2.rect(*PCB_C, *PCB), v2.rect(*PI_C, *v2.PI)]


def labels():
    return [('REV4 PCB (BOVEN, 30 MM)', 3.5, (0, 33.)),
            ('RASPBERRY PI 4 (ONDER)', 3.5, (PI_C[0]-6, PI_C[1])),
            ('USB', 3., (PI_C[0]+v2.PI[0]/2-7, PI_C[1]))]


def geometry():
    v2.BOARDS = []
    plate, cable, mounts, _, _ = v2.build_geometry()
    inner = plate.buffer(-1)
    pp, ip = pcb_points(), pi_points()
    clash = [c for c in cable if any(c.distance(Point(p)) < STANDOFF_R+.8 for p in pp)]
    cable = [c for c in cable if c not in clash]
    for p in pp:
        s = Point(p).buffer(STANDOFF_R)
        assert inner.contains(s), f'Rev4 hole {p} too close to the plate edge'
        assert all(s.distance(o) > .8 for o in cable+mounts), f'Rev4 hole {p} clashes'
    pi = v2.rect(*PI_C, *v2.PI)
    assert inner.contains(pi), 'Pi does not fit'
    assert min(pi.distance(Point(p)) for p in pp) > STANDOFF_R, 'Rev4 standoff hits the Pi'
    for p in ip:
        s = Point(p).buffer(PI_SPACER_R)
        assert inner.contains(s) and all(s.distance(o) > .8 for o in cable+mounts), f'Pi hole {p} clashes'
    holes = [Point(p).buffer(PCB_HOLE/2, quad_segs=16) for p in pp] + \
            [Point(p).buffer(v2.PI_HOLE/2, quad_segs=16) for p in ip]
    return plate, cable, mounts, holes, clash


def build_dxf(path, plate, cable, mounts, holes):
    doc = ezdxf.new('R2010', setup=True); doc.units = ezdxf.units.MM
    doc.layers.add('CUT', color=1); doc.layers.add('ENGRAVE', color=5)
    msp = doc.modelspace()
    for g in [plate, *cable, *mounts, *holes]: v2.add_poly(msp, g, 'CUT')
    for r in outlines(): v2.add_poly(msp, r, 'ENGRAVE')
    for txt, h, c in labels():
        msp.add_text(txt, height=h, dxfattribs={'layer': 'ENGRAVE'}).set_placement(
            c, align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    doc.saveas(path)
    return doc


if __name__ == '__main__':
    plate, cable, mounts, holes, clash = geometry()
    doc = build_dxf(HERE/'electronics_plate_v6.dxf', plate, cable, mounts, holes)
    v2.preview(doc, plate, HERE/'electronics_plate_v6_preview.png', HERE/'electronics_plate_v6.svg')
    v5.outlines, v5.labels = outlines, labels
    v5.build_lbrn(HERE/'electronics_plate_v6.lbrn2', plate, cable, mounts, holes)
    x0, y0, x1, y1 = plate.bounds
    print(f'plate {x1-x0:.1f} x {y1-y0:.1f} mm, {len(cable)} cable openings, {len(clash)} left solid, {len(holes)} board holes')
