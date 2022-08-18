import numpy as np

from . import resistors


def K(amplitude_db):
    return np.power(10., amplitude_db / 20.)


def R_shunt(z0, K):
    return z0 * (K + 1.) / (K - 1.)


def R_series(z0, K):
    return (z0 / 2.) * (K - 1/K)


def Z(resistors):
    r_shunt = resistors['r_shunt']
    r_series = resistors['r_series']
    return np.reciprocal(np.sqrt(
        (np.reciprocal(np.square(r_shunt)) + 2. / (r_shunt * r_series))))


def L_dB(resistors):
    r_shunt = resistors['r_shunt']
    r_series = resistors['r_series']
    gamma = 2. * np.arcsinh(np.sqrt(r_series / (2. * r_shunt)))
    l = np.exp(gamma)
    l_db = 20. * np.log10(l)
    return l_db


def CalculatePiPad(impedance, amplitude_db, series=None):
    k = K(amplitude_db)
    r_shunt = R_shunt(impedance, k)
    r_series = R_series(impedance, k)
    if series:
        r_shunt = resistors.closest_value(r_shunt, series)
        r_series = resistors.closest_value(r_series, series)
    return {'r_shunt': r_shunt, 'r_series': r_series}
