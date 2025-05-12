#!/usr/bin/env python

from enum import IntEnum
import sys
import time

import vxi11


class HP436A:
    class Range(IntEnum):
        Auto = 57
        Range1 = 49             # Most sensitive
        Range2 = 50
        Range3 = 51
        Range4 = 52
        Range5 = 53             # Least sensitive

    class Mode(IntEnum):
        Watt = 65
        dBRel = 66
        dBRef = 67
        dBm = 68
        AutoZero = 90

    class CalFactor(IntEnum):
        Disable = 43            # 100%
        FrontPanel = 45
    
    class Rate(IntEnum):
        Hold = 72
        TriggerWithSettling = 84
        TriggerImmediate = 73
        FreeRunMaxRate = 82
        FreeRunWithSettling = 86

    class StatusOutput(IntEnum):
        MeasurementValid = 80
        WattsModeUnderRange = 81
        OverRange = 82
        dBUnderRange = 83
        AutoZeroNormalRange1 = 84
        AutoZeroNormalOtherRanges = 85
        AutoZeroError = 86

    class RangeOutput(IntEnum):
        Range1 = 73             # Most sensitive
        Range2 = 74
        Range3 = 75
        Range4 = 76
        Range5 = 77             # Least sensitive

    class ModeOutput(IntEnum):
        Watt = 65
        dBRel = 66
        dbRef = 67
        dBm = 68

    def __init__(self, resource_name):
        self.resource_name = resource_name
        self.inst = None

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
            self.inst.close()
        self.inst = None

    def _write_byte(self, b):
        assert self.inst
        self.inst.write_raw(bytes([b]))

    def _read(self):
        assert self.inst
        return self.inst.read_raw(num=14)

    def set_range(self, range: Range):
        self._write_byte(range.value)

    def set_mode(self, mode: Mode):
        self._write_byte(mode.value)

    def set_cal_factor(self, cal_factor: CalFactor):
        self._write_byte(cal_factor.value)

    def set_rate(self, rate: Rate):
        self._write_byte(rate.value)

    def read(self):
        return self.ParseMessage(self._read())

    @classmethod
    def ParseMessage(cls, b: bytes):
        assert len(b) == 14
        status = cls.StatusOutput(b[0])
        range_ = cls.RangeOutput(b[1])
        mode = cls.ModeOutput(b[2])
        assert b[8] == ord('E')
        assert b[9] == ord('-')
        reading = b[3:12]
        value = float(reading)
        assert b[12] == ord('\r')
        assert b[13] == ord('\n')
        return (value, status, range_, mode)

                             
def main(argv):
    resource_name = (argv[1] if len(argv) >= 2
                     else "tcpip::e5810a::gpib0,13::instr")
    
    with HP436A(resource_name) as pm:
        pm.set_range(pm.Range.Auto)
        pm.set_mode(pm.Mode.dBm)
        for _ in range(10):
            pm.set_rate(pm.Rate.TriggerWithSettling)
            reading = pm.read()
            print(reading)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
