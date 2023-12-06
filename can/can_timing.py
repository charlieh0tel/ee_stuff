#!/usr/bin/python3

import argparse
import contextlib
import can
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clock_rate", type=float, required=True)
    parser.add_argument("--nom_bitrate", type=float, default=1_000_000)
    parser.add_argument("--data_bitrate", type=float, default=2_000_000)
    args = parser.parse_args()

    timings = set()

    for sample_point in range(50, 100):
        with contextlib.suppress(ValueError):
            timings.add(
                can.BitTimingFd.from_sample_point(
                    f_clock=args.clock_rate,
                    nom_bitrate=args.nom_bitrate,
                    nom_sample_point=sample_point,
                    data_bitrate=args.data_bitrate,
                    data_sample_point=sample_point))

    for timing in sorted(timings, key=lambda x: x.nom_sample_point):
        print(timing)

    return 0


if __name__ == "__main__":
    sys.exit(main())
