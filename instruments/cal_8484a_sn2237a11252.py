#!/usr/bin/env python

import sys

import cal_rf_sensor


SENSOR_INFO = cal_rf_sensor.SensorInfo(
    model="8484A",
    serial="2237A11252",
    min_dBm=-65.,
    max_dBm=-20.,
    cal_points=[
        (0.050e9, 97.0),
        (0.100e9, 95.0),
        (0.500e9, 94.5),
        (1.000e9, 94.0),
        (2.000e9, 93.5),
        (3.000e9, 93.0),
        (4.000e9, 92.5),
        (5.000e9, 92.0),
        (6.000e9, 91.5),
        (7.000e9, 91.0),
        (8.000e9, 91.0),
        (9.000e9, 91.0),
        (10.000e9, 91.0),
        (11.000e9, 91.0),
        (12.000e9, 91.5),
        (13.000e9, 92.0),
        (14.000e9, 92.0),
        (15.000e9, 93.5),
        (16.000e9, 96.0),
        (17.000e9, 96.0),
        (18.000e9, 98.5)
    ]
)


def main(argv):
    return cal_rf_sensor.run(argv, SENSOR_INFO, [-30.])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
