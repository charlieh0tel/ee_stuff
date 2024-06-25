# Really crappy code.

L=35.60
W=19.00
LPITCH=4.45

FP="""
(footprint "SA8x8"
	(version 20240108)
	(generator "pcbnew")
	(generator_version "8.0")
	(layer "F.Cu")
	(property "Reference" "REF**"
		(at 0 -0.5 0)
		(unlocked yes)
		(layer "F.SilkS")
		(uuid "b0c25602-b4fe-4314-a794-39ada28a59bd")
		(effects
			(font
				(size 1 1)
				(thickness 0.1)
			)
		)
	)
	(property "Value" "SA8x8"
		(at 0 1 0)
		(unlocked yes)
		(layer "F.Fab")
		(uuid "6b36fe48-c912-4223-8d4c-8bb305bb88ba")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(property "Footprint" ""
		(at 0 0 0)
		(unlocked yes)
		(layer "F.Fab")
		(hide yes)
		(uuid "ab4fc620-da9f-4913-ad8c-8543d333cb63")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(property "Datasheet" ""
		(at 0 0 0)
		(unlocked yes)
		(layer "F.Fab")
		(hide yes)
		(uuid "a1e7d6db-f6e4-437f-845f-96e2ee673733")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(property "Description" ""
		(at 0 0 0)
		(unlocked yes)
		(layer "F.Fab")
		(hide yes)
		(uuid "caaf3efc-3cda-47a6-9041-de72bd12e778")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)

			)
		)
	)
	(attr smd)
	(fp_rect
		(start 0 0)
		(end 35.6 19)
		(stroke
			(width 0.25)
			(type default)
		)
		(fill none)
		(layer "Dwgs.User")
		(uuid "e3fec57d-59fa-40cc-929c-6aca37d03aa9")
	)
	(fp_text user "${{REFERENCE}}"
		(at 0 2.5 0)
		(unlocked yes)
		(layer "F.Fab")
		(uuid "6a440e22-721f-490d-97dc-b54993edba13")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
{0}
)
"""


def pad(n, x, y, size):
    return f"""(pad "{n}" smd roundrect
		(at {x:.2f} {y:.2f})
		(size {size[0]} {size[1]})
		(layers "F.Cu" "F.Paste" "F.Mask")
		(roundrect_rratio 0.25)
		(thermal_bridge_angle 45))"""

def pads_left():
    pads = []
    for pin in range(1, 8):
        pads.append(pad(pin, L - LPITCH * pin, W, size=(2, 4)))
    return pads

def pads_right():
    pads = []
    for pin in range(12, 19):
        pads.append(pad(pin, LPITCH * (pin - 11), 0, size=(2, 4)))
    return pads

def pads_top():
    pads = []
    pitch = 4.6
    y_offset = 2.54
    for pin in range(8, 12):
        pads.append(pad(pin, 0, y_offset + pitch * (11 - pin), size=(4, 2)))
    return pads

"""
def pads_bottom():
    pad_w = 4.
    return [pad(19, L, W - 4, size=(pad_w, 8.00)),
            pad(20, L, 3.30, size=(pad_w, 6.60))]
"""

def pads_thermal():
    # guess
    return [pad(21, 1.25 * LPITCH, W / 2.0, size=(6.0, 5.5))]

def pads():
    return (pads_left() +
            pads_right() +
            pads_top() +
            pads_thermal())

def footprint():
    return FP.format("\n".join(pads()))

def go():
    with open("SA8x8.kicad_mod", 'w') as f:
        print(footprint(), file=f)

go()
