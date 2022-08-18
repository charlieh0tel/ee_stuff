#!/usr/bin/python3

import numpy as np

from common import pi_pad


# TODO(charliehotel): pick up defaults from command line.
def Main(impedance=50,
         pad_dbs=[1, 2, 3, 6, 9, 10, 20],
         series=['', 'E24', 'E48', 'E96', 'E192']):
    print("                                   ")
    print("          R_series                 ")
    print("  --------/\/\/\/\---------        ")
    print("      |              |             ")
    print("      \              \             ")
    print("      / R_shunt      / R_shunt     ")
    print("      \              \             ")
    print("      |              |             ")
    print("      _              _             ")
    print()
    for pad_db in pad_dbs:
        print(f"{pad_db} dB:")
        for s in series:
            resistors = pi_pad.CalculatePiPad(impedance, pad_db, s)
            r_shunt = resistors['r_shunt']
            r_series = resistors['r_series']
            z = pi_pad.Z(resistors)
            z_error = np.abs(z - impedance) / impedance
            print(f"  {s:4s} R_shunt={r_shunt:.3f} R_series={r_series:.3f}, "
                  f"Z={z:.3f}, Z_err={z_error * 100.:.2f} %")
        print()


if __name__ == "__main__":
    Main()
