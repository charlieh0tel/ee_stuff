#!/usr/bin/env python

import sys

import pyvisa

import rs_smb100a


def main(argv):
    rm = pyvisa.ResourceManager('@py')
    #resources = rm.list_resources()
    #print(resources)

    resource_name = (argv[1] if len(argv) >= 2
                     else "TCPIP::rssmb100a180609.local::INSTR")

    with rs_smb100a.RhodeSchwarzSMB100A(rm, resource_name) as siggen:
        siggen.reset()
        siggen.system_preset()

        test_points_ghz_cf=[
            (0.050, 97.0),
            (0.100, 95.0),
            (0.500, 94.5),
            (1.000, 94.0),
            (2.000, 93.5),
            (3.000, 93.0),
            (4.000, 92.5),
            (5.000, 92.0),
            (6.000, 91.5),
            (7.000, 91.0),
            (8.000, 91.0),
            (9.000, 91.0),
            (10.000, 91.0),
            (11.000, 91.0),
            (12.000, 91.5),
            (13.000, 92.0),
            (14.000, 92.0),
            (15.000, 93.5),
            (16.000, 96.0),
            (17.000, 96.0),
            (18.000, 98.5)]

        try:
            siggen.set_power(-40.)
            siggen.set_output(True)
            for (ghz, cf) in test_points_ghz_cf:
                siggen.set_frequency(ghz * 1e9)
                print(f"frequency set to {ghz} GHz")
                print(f"set cf to {round(cf)} %")
                input("record reading and press return -> ")
                print()
        finally:
            siggen.set_output(False)
    
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
