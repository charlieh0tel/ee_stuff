# TODO

- Verify the +9V thermal max (250 mA in `power_tree.json`) against the
  actual layout: it assumes the LM2940 TO-263 sits on a copper pour giving
  θJA ≈ 50 °C/W (Tj 125 °C, Ta 50 °C, 15 V in). Recompute once the pour is
  drawn.

- Power budget checking — `tools/check_power.py` exists (extracts `Load_mA`
  per rail via the netlist, alerts at `alert_utilization`, exits nonzero on
  OVER). Remaining:
  - Annotate `Load_mA` on the rest of the loads as the preamp / TX / RX /
    keying sheets get drawn (only U2, U3 on the supply sheet are done).
  - `--update`: sync `power_tree.json` from the extracted loads and
    regenerate the tree sheet (needs a per-load ref linkage first; the json
    `loads` list is still freeform functional groupings, so the current
    reconciliation is advisory-only).
  - Wire `check_power.py` into CI so a schematic edit that blows a budget
    fails the build.
