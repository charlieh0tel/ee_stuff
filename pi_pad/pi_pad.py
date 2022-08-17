#!/usr/bin/python3

import numpy as np

import resistors


def K(amplitude_db):
    return 10.**(amplitude_db/20)


def R1(z0, K):
    return z0 * (K + 1.) / (K - 1.)


def R2(z0, K):
    return (z0 / 2.) * (K - 1/K)


def Z(r1, r2):
    return np.reciprocal(np.sqrt(
        (np.reciprocal(np.square(r1)) + 2. / (r1 * r2))))


def pi_pad(impedance, amplitude_db, series=None):
    k = K(amplitude_db)
    r1 = R1(impedance, k)
    r2 = R2(impedance, k)
    if series:
        r1 = resistors.closest_value(r1, series)
        r2 = resistors.closest_value(r2, series)
    return (r1, r2)


def dump(impedance=50,
         pad_dbs=[1, 2, 3, 6, 9, 10, 20],
         series=['', 'E24', 'E48', 'E96', 'E192']):
    for pad_db in pad_dbs:
        print(f"{pad_db} dB")
        for s in series:
            (r1, r2) = pi_pad(impedance, pad_db, s)
            z = Z(r1, r2)
            z_error = np.abs(z - impedance) / impedance
            print(f"  {s:4s} r1={r1:.3f} r2={r2:.3f}, Z={z:.3f}, "
                  f"Z_err={z_error * 100.:.2f} %")
        print()


if __name__ == "__main__":
    dump()
