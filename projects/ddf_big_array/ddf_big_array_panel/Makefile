all: ddf_big_array_antterm_panel.kicad_pcb ddf_big_array_antsw_panel.kicad_pcb


ddf_big_array_antterm_panel.kicad_pcb: ../ddf_big_array_antterm/ddf_big_array_antterm.kicad_pcb
	kikit panelize \
    --layout 'grid; rows: 2; cols: 2; space: 2mm' \
    --tabs 'fixed; width: 3mm; vcount: 2' \
    --cuts 'mousebites; drill: 0.5mm; spacing: 1mm; offset: 0.2mm; prolong: 0.5mm' \
    --framing 'frame; width: 5mm; space: 3mm; cuts: both' \
    --post 'millradius: 1mm' \
    $< $@

ddf_big_array_antsw_panel.kicad_pcb: ../ddf_big_array_antsw/ddf_big_array_antsw.kicad_pcb
	kikit panelize \
    --layout 'grid; rows: 1; cols: 1; space: 2mm' \
    --tabs 'fixed; width: 3mm; vcount: 2' \
    --cuts 'mousebites; drill: 0.5mm; spacing: 1mm; offset: 0.2mm; prolong: 0.5mm' \
    --framing 'frame; width: 11mm; space: 3mm; cuts: both' \
    --post 'millradius: 1mm' \
    $< $@


.PHONY: clean
clean:
	rm -f ddf_big_array_antterm_panel.* \
	      ddf_big_array_antsw_panel.* \
              fp-info-cache

