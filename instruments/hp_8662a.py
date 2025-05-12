#!/usr/bin/env python

import sys
import time

import vxi11


class HP8662A:
    def __init__(self, resource_name):
        self.resource_name = resource_name
        self.inst = None
        self.power_dBm = None
        self.first_ap_quirk = True

    def __enter__(self, *args):
        return self.open(*args)

    def __exit__(self, *args):
        self.close()

    def open(self):
        assert self.inst is None
        self.inst = vxi11.Instrument(self.resource_name)
        self.inst.clear()
        return self

    def close(self):
        if self.inst:
            self.inst.local()
            self.inst.close()
        self.inst = None

    def _write_string(self, s):
        assert self.inst
        # print(s)
        self.inst.write_raw(s.encode('ascii'))

    def reset(self):
        assert self.inst

    def system_preset(self):
        assert self.inst
        self._write_string("SP00\n")
        time.sleep(0.1)
        self._write_string("AO\n")

    def set_frequency(self, frequency_hz: float):
        assert self.inst
        self._write_string(f"FR{frequency_hz}HZ\n")

    def set_output(self, on: bool):
        assert self.inst
        if on:
            assert self.power_dBm is not None
            ap = f"AP{self.power_dBm:.1f}DM\n"
            self._write_string(ap)
            if self.first_ap_quirk:
                self._write_string(ap)
                self.first_ap_quirk = False
        else:
            self._write_string(f"AO\n")

    def set_power(self, power_dBm: float):
        self.power_dBm = power_dBm


def main(argv):
    resource_name = (argv[1] if len(argv) >= 2
                     else "tcpip::e5810a::gpib0,25::instr")

    with HP8662A(resource_name) as siggen:
        siggen.reset()
        siggen.system_preset()
        freq_hz = 150e6
        power_dBm = -22.
        print(f"setting siggen for {freq_hz} Hz @ {power_dBm} dBm")
        siggen.set_frequency(freq_hz)
        try:
            print("power on")
            siggen.set_power(power_dBm)
            siggen.set_output(True)
            print("...")
            time.sleep(5)
            print("power off")
            siggen.set_output(False)
            time.sleep(5)
            print("power on")
            siggen.set_output(True)
            print("...")
            time.sleep(5)
        finally:
            print("power off")
            siggen.set_output(False)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
