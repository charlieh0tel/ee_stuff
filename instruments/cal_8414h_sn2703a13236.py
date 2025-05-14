#!/usr/bin/env python

import sys

import cal_rf_sensor


SENSOR_INFO = cal_rf_sensor.SensorInfo(
    model="84841H",
    serial="2703A13236",
    min_dBm=-10.,
    max_dBm=35.,
    cal_points=[
        # (Hz, Cf%, Rho)
        (0.1000e9, 99.4, 0.014),
        (2.00e9, 97.3, 0.016),
        (3.00e9, 96.8, 0.017),
        (4.00e9, 96.3, 0.017),
        (5.00e9, 96.4, 0.014),
        (6.00e9, 96.7, 0.011),
        (7.00e9, 97.1, 0.016),
        (8.00e9, 97.3, 0.023),
        (9.00e9, 97.7, 0.024),
        (10.00e9, 98.2, 0.015),
        (11.00e9, 97.6, 0.009),
        (12.40e9, 97.8, 0.024),
        (13.00e9, 97.1, 0.028),
        (14.00e9, 96.3, 0.036),
        (15.00e9, 95.5, 0.061),
        (16.00e9, 86.0, 0.123),
        (17.00e9, 87.3, 0.091),
        (18.00e9, 91.6, 0.112)]
)


def main(argv):
    return cal_rf_sensor.run(argv, SENSOR_INFO,
                             [-5., 0., 10., 15., 20., 25., 30.])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
