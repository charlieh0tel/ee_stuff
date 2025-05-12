#!/usr/bin/env python

import sys

import cal_rf_sensor


SENSOR_INFO = cal_rf_sensor.SensorInfo(
    model="8482A",
    serial="2652A12432",
    min_dBm=-30.,
    max_dBm=20.,
    cal_points=[
        (0.100e6, 97.8),
        (0.300e6, 99.7),
        (1.000e6, 99.4),
        (3.000e6, 98.7),
        (10.000e6, 98.7),
        (30.000e6, 98.3),
        (100.000e6, 97.9),
        (300.000e6, 97.5),
        (1000.000e6, 97.1),
        (2000.000e6, 96.0),
        (3000.000e6, 90.3),
        (4200.000e6, 86.6)
    ]
)


def main(argv):
    return cal_rf_sensor.run(argv, SENSOR_INFO,
                             [-20., -10., 0., 10., 20.])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
