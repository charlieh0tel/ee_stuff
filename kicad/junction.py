#!/usr/bin/python3

import sys
import math

def generate(n, radius, origin=(0., 0.), angle_start=0.):
    dangle = 360. / n
    print("ang_deg        tx_orig        y_orig"
          "         tx             ty")
    for i in range(n):
        angle = angle_start + i * dangle;
        pt = (origin[0] + radius * math.cos(math.radians(angle)),
              origin[1] + radius * math.sin(math.radians(angle)))
        print(f"{angle:14f} {origin[0]:14f} {origin[1]:14f} "
              f"{pt[0]:14f} {pt[1]:14f}")
    

def main(argv):
    if len(argv) != 3:
        print(f"usage: {argv[0]} n radius", file=sys.stderr)
        return 1
    n = int(argv[1])
    radius = float(argv[2])
    generate(n, radius)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
