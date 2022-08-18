#!/usr/bin/python3

import numpy as np

import resistors


def K(amplitude_db):
    return 10.**(amplitude_db/20)


def R_shunt(z0, K):
    return z0 * (K + 1.) / (K - 1.)


def R_series(z0, K):
    return (z0 / 2.) * (K - 1/K)


def Z(resistors):
    r_shunt = resistors['r_shunt']
    r_series = resistors['r_series']
    return np.reciprocal(np.sqrt(
        (np.reciprocal(np.square(r_shunt)) + 2. / (r_shunt * r_series))))


def pi_pad(impedance, amplitude_db, series=None):
    k = K(amplitude_db)
    r_shunt = R_shunt(impedance, k)
    r_series = R_series(impedance, k)
    if series:
        r_shunt = resistors.closest_value(r_shunt, series)
        r_series = resistors.closest_value(r_series, series)
    return {'r_shunt': r_shunt, 'r_series': r_series}


def dump(impedance=50,
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
            resistors = pi_pad(impedance, pad_db, s)
            r_shunt = resistors['r_shunt']
            r_series = resistors['r_series']
            z = Z(resistors)
            z_error = np.abs(z - impedance) / impedance
            print(f"  {s:4s} R_shunt={r_shunt:.3f} R_series={r_series:.3f}, "
                  f"Z={z:.3f}, Z_err={z_error * 100.:.2f} %")
        print()


if __name__ == "__main__":
    dump()
