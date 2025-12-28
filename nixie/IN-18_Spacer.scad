$fn = 120;

spacer_height = 7;        // contacts stand 6.2mm off board, need clearance
pin_circle_dia = 18;
pin_entry_r = 0.7;        // 1.4mm dia, matches lead forming tool
contact_hole_r = 1.0;     // 2.0mm dia to clear PCBA contacts
taper_depth = 1.5;        // depth of tapered entry section
wall_thickness = 2;       // minimum wall around pin holes
notch_size = 1.2;         // reduced from 2mm for smaller diameter

// Minimized diameter: pin circle radius + contact hole + wall
base_dia = pin_circle_dia + (contact_hole_r * 2) + (wall_thickness * 2);

difference() {
    // Main body
    cylinder(h = spacer_height, d = base_dia, center = true);

    // 14 pin holes in 15-position pattern (key gap between pin 14 and pin 1)
    for (i = [0 : 13]) {
        angle = 90 - (i * (360 / 15));

        translate([
            (pin_circle_dia / 2) * cos(angle),
            (pin_circle_dia / 2) * sin(angle),
            0
        ])
        union() {
            // Tapered entry from top
            translate([0, 0, spacer_height/2 - taper_depth/2])
                cylinder(h = taper_depth + 0.1, r1 = pin_entry_r, r2 = contact_hole_r, center = true);
            // Main clearance hole for contacts
            translate([0, 0, -taper_depth/2])
                cylinder(h = spacer_height - taper_depth + 0.1, r = contact_hole_r, center = true);
        }
    }

    // Alignment notch
    translate([0, (base_dia/2), 0])
    rotate([0, 0, 45])
    cube([notch_size, notch_size, spacer_height + 2], center = true);
}
