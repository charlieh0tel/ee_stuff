// IN-18 Lead Former - Notch Aligned to Pin 1
// 14 positions, 13 pins (Gap between Pin 1 and Pin 13/14)

$fn = 100; 

// Dimensions
base_dia = 42;
base_height = 8;
pin_circle_dia = 30; 
pin_hole_r = 0.9;
center_hole_dia = 22; 
notch_size = 2;

difference() {
    // Main Body
    cylinder(h = base_height, d = base_dia, center = true);
    
    // Exhaust Tip Clearance
    cylinder(h = base_height + 2, d = center_hole_dia, center = true);
    
    // Pin Holes
    for (i = [1 : 13]) { // Pin 1 through Pin 13
        // Calculation to place Pin 1 exactly at 90 degrees (Top)
        angle = 90 - ((i-1) * (360 / 14)); 
        
        translate([
            (pin_circle_dia / 2) * cos(angle),
            (pin_circle_dia / 2) * sin(angle),
            0
        ])
        union() {
            // Tapered top
            translate([0,0,1]) 
                cylinder(h = base_height/2, r1 = pin_hole_r, r2 = pin_hole_r + 1);
            // Main hole
            cylinder(h = base_height + 2, r = pin_hole_r, center = true);
        }
    }

    // Pin 1 Notch.
    translate([0, (base_dia/2), 0])
    rotate([0, 0, 45])
    cube([notch_size, notch_size, base_height + 2], center = true);
}