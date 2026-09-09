# Vendor datasheets

Reference copies of the datasheets the design decisions in DESIGN.md,
LEVELS.md and the schematic `MPN` fields rely on. Vendor documents,
their copyright; kept here so the design is reviewable offline and so
a silently revised datasheet cannot move the ground under a finished
board. Fetched 2026-09-08 unless noted.

| File | Part(s) / use in TBox | Source |
|---|---|---|
| ADI_ADP7142.pdf | ADP7142AUJZ-5.0 (U2501, BIAS_5V) | analog.com via web.archive.org (site blocks scripted fetches) |
| Bourns_3386.pdf | 3386W-1-103LF trims (RV33xx, RV34xx) | bourns.com |
| Bourns_SMAJ.pdf | SMAJ15A / SMAJ15CA TVS (rear I/O) | bourns.com (Littelfuse site blocks scripted fetches; same JEDEC part) |
| Bourns_SMBJ.pdf | SMBJ18A TVS (D2502, supply input) | bourns.com (as above) |
| CK_7000-series_toggles.pdf | 7101MD9AV2BE rear toggles, 7201MD9V6BE override | ckswitches.com (fetched 2026-09-04) |
| CK_PVA.pdf | PVA1EEH2 / PVA1OAH2 pushbuttons (SW21xx, SW2201) | ckswitches.com via web.archive.org |
| Diodes_1N4148W.pdf | 1N4148W (keying/diode logic) | diodes.com |
| Diodes_2N7002.pdf | 2N7002 (keying logic) | diodes.com |
| Diodes_MMBT3904.pdf | MMBT3904 (Q2201) | diodes.com |
| Hammond_560G_transformer.pdf | 560G — evaluated for line-out isolation, not used | hammondmfg.com (2026-09-04) |
| JST_XH.pdf | B2B-XH-A (J2501 Powerpole pigtail), B4B-XH-A (J1104/J1304) | jst-mfg.com |
| Keystone_5015.pdf | 5015 SMT test points | keyelco.com |
| Littelfuse_1812L_PTC.pdf | 1812L050/60DR (F2501) | littelfuse.com via web.archive.org |
| Neutrik_jacks_circuits.pdf | NRJ6HM-1-PRE / NRJ6HF-1 contact arrangements (the page showing which jacks bond sleeve to panel) | neutrik.com (2026-09-04) |
| Neutrik_NRJ6HF-1.pdf | NRJ6HF-1 phones jacks (J1002/J1004) — "sleeve contact / frontpanel connection": bonds GND to the panel (review 2026-09-08 #7) | neutrik.com (2026-09-08, by hand) |
| Neutrik_NRJ6HM-1-PRE.pdf | NRJ6HM-1-PRE chassis-bonded 1/4" jacks (J1102/J1302/J3202/J3204) | neutrik.com (2026-09-08, by hand) |
| Neutrik_NJ6FD-V.pdf | NJ6FD-V — isolated plastic vertical jack, candidate considered for the phones jacks | neutrik.com (2026-09-08, by hand) |
| Rean_NYS216.pdf | NYS216 — isolated plastic-housing horizontal 1/4" jack with nut, candidate for the phones jacks | neutrik.com (2026-09-08, by hand) |
| Rean_NYS229.pdf | NYS229 — mono variant of the above | neutrik.com (2026-09-08, by hand) |
| Nisshinbo_NJM4556A.pdf | NJM4556AM phones amplifiers (U2401, U2403) | nisshinbo-microdevices.co.jp |
| SameSky_SJ1-353xNG.pdf | SJ1-3533NG isolated 3.5 mm jacks (J1001/J1003/J3303) | sameskydevices.com |
| SameSky_SJ-4351X.pdf | SJ-43514 TRRS headset jacks (J1103/J1303) | cuidevices.com (2026-09-06) |
| Switchcraft_3.5mm_jacks_catalog.pdf | 35RAPC family catalog pages | switchcraft.com (2026-09-04) |
| Switchcraft_35RAPC__H3_drawing.pdf | 35RAPC2AH3 / 35RAPC2BH3 drawing rev J (source of the tbox.pretty footprint) | switchcraft.com (2026-09-04) |
| TI_OPA1678.pdf | OPA1678IDR op-amps | ti.com (2026-09-04) |
| TI_TPS7A47.pdf | TPS7A4701RGWR +9 V regulator (U2503), SBVS204G rev. May 2026 | ti.com |
| TI_TS12A12511.pdf | TS12A12511DGKR mute switches | ti.com (2026-09-04) |
| TI_OPA1622.pdf | OPA1622IDRCR headphone amplifiers (U2401/U2403, review Q2) | ti.com (2026-09-08) |
| TI_TPS3808.pdf | TPS3808G01DBVR supply supervisor (U2504, review Q4), SBVS050N rev. Aug 2026 | ti.com (2026-09-08) |
| Littelfuse_SP724.pdf | SP724AHTG ESD clamp arrays at the jacks (U1001, U1103/U1104, U1303/U1304, U3201; review Q8) | littelfuse.com via web.archive.org (2026-09-08) |
| Triad_TY-250P.pdf | TY-250P line-out transformers (T3301/T3302), 2019-05-31 drawing | triadmagnetics.com (2026-09-04) |
| Vishay_SS32-SS36.pdf | SS34 (D2501, reverse-supply) | vishay.com |

Not yet collected (vendor and distributor sites reject non-browser
fetches and the Wayback Machine has no copy): Alpha RD901F-40 /
RD902F-40 9 mm pot drawings (the stock KiCad footprints were built from
them) — mouser.com/datasheet/3/140/1/RD901F.pdf.
