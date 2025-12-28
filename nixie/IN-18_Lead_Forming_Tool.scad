$fn = 120; 

base_height = 8;          
base_dia = 36;
pin_circle_dia = 18;      
pin_hole_r = 0.7;           // oversized for FDM/PETG shrinkage        
center_hole_dia = 10;    
notch_size = 2;          

difference() {
    // Main body.
    cylinder(h = base_height, d = base_dia, center = true);
    
    // Center clearance for tip
    cylinder(h = base_height + 2, d = center_hole_dia, center = true);
    
    // 14 pin holes in 15-position pattern (key gap between pin 14 and pin 1)
    for (i = [0 : 13]) {
        angle = 90 - (i * (360 / 15)); 
        
        translate([
            (pin_circle_dia / 2) * cos(angle),
            (pin_circle_dia / 2) * sin(angle),
            0
        ])
        union() {
            // Tapered lead-in
            translate([0,0,base_height/2 - 1]) 
                cylinder(h = 2.1, r1 = pin_hole_r, r2 = pin_hole_r + 0.4, center = true);
            // Pin alignment hole
            cylinder(h = base_height + 2, r = pin_hole_r, center = true);
        }
    }

    // Alignment notch
    translate([0, (base_dia/2), 0])
    rotate([0, 0, 45])
    cube([notch_size, notch_size, base_height + 2], center = true);
    
    // Engraved Pin 1
    translate([0, 14, base_height/2 - 0.5])
    linear_extrude(1.1)
    text("1", size = 2.25, halign = "center", valign = "center", font="Liberation Sans:style=Bold");
}
