#!/usr/bin/env python

import sys
import time

import pyvisa


class RhodeSchwarzSMB100A:
    def __init__(self, resource_manager, resource_name):
        self.resource_manager = resource_manager
        self.resource_name = resource_name
        self.inst = None

    def __enter__(self, *args):
        return self.open(*args)

    def __exit__(self, *args):
        self.close()

    def open(self):
        assert self.inst is None
        self.inst = self.resource_manager.open_resource(self.resource_name)
        return self

    def close(self):
        if self.inst:
            self.inst.close()
        self.inst = None

    def reset(self):
        assert self.inst
        self.inst.write("*RST")

    def system_preset(self):
        assert self.inst
        self.inst.write(":SYS:PRESET")

    def set_output(self, on: bool):
        assert self.inst
        self.inst.write(f":OUTPUT {int(on)}")

    def set_frequency(self, frequency_hz: float):
        assert self.inst
        self.inst.write(f":FREQ {frequency_hz}")

    def set_power(self, power_dBm: float):
        assert self.inst
        self.inst.write(f":POWER {power_dBm}")


def main(argv):
    rm = pyvisa.ResourceManager('@py')
    #resources = rm.list_resources()
    #print(resources)

    resource_name = (argv[1] if len(argv) >= 2
                     else "TCPIP::rssmb100a180609.local::INSTR")

    with RhodeSchwarzSMB100A(rm, resource_name) as siggen:
        siggen.reset()
        siggen.system_preset()
        freq_hz = 15e6
        power_dbm = -40.
        print(f"setting siggen for {freq_hz} Hz @ {power_dbm} dBm")
        siggen.set_frequency(freq_hz)
        try:
            siggen.set_power(power_dbm)
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
