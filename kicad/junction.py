#!/usr/bin/python3

import sys
import math
import argparse

def generate_lines(n, radius, origin=(0., 0.), angle_start_deg=0., kicad=False):
    dangle = 360. / n
    if not kicad:
        print("       ang_deg             x0             y0"
              "            x1             y1")
    for i in range(n):
        angle = math.fmod(angle_start_deg + i * dangle, 360.);
        angle_rad = math.radians(90. - angle)
        (x0, y0) = origin
        (x1, y1) = (x0 + radius * math.cos(angle_rad),
                    y0 + radius * math.sin(angle_rad))
        if kicad:
            print(f"(fp_line (start {x0:f} {y0:f}) (end {x1:f} {y1:f}) (layer \"F.Cu\") (width 0.2))")
        else:
            print(f"{angle:14f} {x0:14f} {y0:14f}) {x1:14f} {y1:14f}")

def generate_polys(n, radius, width, origin=(0., 0.), angle_start_deg=0., kicad=False):
    dangle = 360. / n
    half_width = width / 2.
    if not kicad:
        print("       ang_deg             x0             y0"
              "            x1             y1             x2"
              "            y2             x3             y3")

    for i in range(n):
        angle = math.fmod(angle_start_deg + i * dangle, 360.);
        angle_rad = math.radians(90. - angle)
        (lx0, ly0) = origin
        (lx1, ly1) = (lx0 + radius * math.cos(angle_rad),
                      ly0 + radius * math.sin(angle_rad))
        (dx, dy) = (half_width * math.sin(-angle_rad),
                    half_width * math.cos(-angle_rad))
        (x0, y0) = (lx0 - dx, ly0 - dy)
        (x1, y1) = (lx0 + dx, ly0 + dy)
        (x2, y2) = (lx1 + dx, ly1 + dy)
        (x3, y3) = (lx1 - dx, ly1 - dy)
        if kicad:
            print(f"(fp_poly (pts (xy {x0:f} {y0:f}) (xy {x1:f} {y1:f}) (xy {x2:f} {y2:f}) (xy {x3:f} {y3:f})) "
                  "(width 00.) (layer \"F.Cu\") (fill solid))")
        else:
            print(f"{angle:14f} {x0:14f} {y0:14f} {x1:14f} {y1:14f}"
                  f"{x2:14f} {y2:14f} {x3:14f} {y3:14f}")
    
def main(argv):
    parser = argparse.ArgumentParser(prog=argv[0])
    parser.add_argument('n', type=int)
    parser.add_argument('radius', type=float)
    parser.add_argument('-w', '--width', type=float)
    parser.add_argument('-a', '--angle_start_deg', type=float, default=0.)
    parser.add_argument('-k', '--kicad', action='store_true')
    args = parser.parse_args(argv[1:])

    if args.kicad:
        # invert y for kicad
        args.angle_start_deg -= 180.
        
    if args.width:
        generate_polys(args.n, args.radius, args.width, 
                       angle_start_deg=args.angle_start_deg, kicad=args.kicad)
    else:
        generate_lines(args.n, args.radius,
                       angle_start_deg=args.angle_start_deg, kicad=args.kicad)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
