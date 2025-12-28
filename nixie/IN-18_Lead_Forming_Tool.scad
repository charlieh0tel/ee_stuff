<<<<<<< HEAD
// Precision IN-18 Lead Former - Clean Geometry
// Center hole: 10mm | Notch: 2mm | Pin Circle: 27mm

$fn = 120; 

// Dimensions
base_dia = 28;
base_height = 8;
pin_circle_dia = 18;     
pin_hole_r = 0.55;
=======
$fn = 120; 

base_height = 8;          
base_dia = 30;            
pin_circle_dia = 18;      
pin_hole_r = 0.55;        
>>>>>>> 9c408dc (Was b0rken; maybe fixed?)
center_hole_dia = 10;    
notch_size = 2;          

difference() {
    // Main body
    cylinder(h = base_height, d = base_dia, center = true);
    
<<<<<<< HEAD
    // Center Hole
    cylinder(h = base_height + 2, d = center_hole_dia, center = true);
    
    // Pin Holes (13 pins at 14 positions)
    for (i = [0 : 12]) { 
        // Pin 1 starts at 90 degrees (Top/North)
=======
    // Center clearance for tip
    cylinder(h = base_height + 2, d = center_hole_dia, center = true);
    
    // 13 pin holes arranged in a 14-position circular pattern
    for (i = [0 : 12]) { 
>>>>>>> 9c408dc (Was b0rken; maybe fixed?)
        angle = 90 - (i * (360 / 14)); 
        
        translate([
            (pin_circle_dia / 2) * cos(angle),
            (pin_circle_dia / 2) * sin(angle),
            0
        ])
        union() {
<<<<<<< HEAD
            // Tapered entry
            translate([0,0,1]) 
                cylinder(h = base_height/2, r1 = pin_hole_r, r2 = pin_hole_r + 0.8);
            // Main hole
=======
            // Tapered lead-in
            translate([0,0,base_height/2 - 1]) 
                cylinder(h = 2.1, r1 = pin_hole_r, r2 = pin_hole_r + 0.4, center = true);
            // Pin hole
>>>>>>> 9c408dc (Was b0rken; maybe fixed?)
            cylinder(h = base_height + 2, r = pin_hole_r, center = true);
        }
    }

<<<<<<< HEAD
    // Index Notch (Aligned with Pin 1)
    translate([0, (base_dia/2), 0])
    rotate([0, 0, 45])
    cube([notch_size, notch_size, base_height + 2], center = true);
}
=======
    // Alignment notch
    translate([0, (base_dia/2), 0])
    rotate([0, 0, 45])
    cube([notch_size, notch_size, base_height + 2], center = true);
    
    // Engraved pin 1 identifier
    translate([0, 12, base_height/2 - 0.5])
    linear_extrude(1.1)
    text("1", size = 1.8, halign = "center", valign = "center", font="Liberation Sans:style=Bold");
}
>>>>>>> 9c408dc (Was b0rken; maybe fixed?)
