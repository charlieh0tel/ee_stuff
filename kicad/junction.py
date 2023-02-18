import sys
import math

def generate(n, radius, origin=(0., 0.), angle_start=0.):
    dangle = 360. / n
    for i in range(n):
        angle = angle_start + i * dangle;
        pt = (origin[0] + radius * math.cos(math.radians(angle)),
              origin[1] + radius * math.sin(math.radians(angle)))
        print(f"{origin[0]:f} {origin[1]:f} {pt[0]:f} {pt[1]:f}")
    
    return 0
