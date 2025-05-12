#!/usr/bin/env python

import dataclasses
import datetime
import sys
import time

import pandas as pd
import pyvisa

import rs_smb100a
import hp_436a


DEFAULT_SIG_GEN_RESOURCE="TCPIP::rssmb100a180609.local::INSTR"
DEFAULT_POWER_METER_RESOURCE="TCPIP::e5810a::gpib0,13::INSTR"


@dataclasses.dataclass
class SensorInfo:
    model: str
    serial: str
    min_dBm: float
    max_dBm: float
    cal_points: list([float, float])


def run(argv, sensor_info, power_levels_dBm):
    rm = pyvisa.ResourceManager('@py')

    sig_gen_resource = (argv[1] if len(argv) >= 2
                        else DEFAULT_SIG_GEN_RESOURCE)
    power_meter_resource = (argv[2] if len(argv) >= 3
                            else DEFAULT_POWER_METER_RESOURCE)

    readings=[]
    with rs_smb100a.RhodeSchwarzSMB100A(rm, sig_gen_resource) as siggen:
        siggen.reset()
        siggen.system_preset()

        siggen.set_output(False)

        try:
            with hp_436a.HP436A(power_meter_resource) as pm:
                pm.set_range(pm.Range.Auto)
                pm.set_mode(pm.Mode.dBm)
                pm.set_cal_factor(pm.CalFactor.Disable)

                for power_level_dBm in power_levels_dBm:
                    assert sensor_info.min_dBm <= power_level_dBm <= sensor_info.max_dBm
                    siggen.set_output(False)
                    siggen.set_power(power_level_dBm)
                    siggen.set_output(True)

                    for (hz, cf) in sensor_info.cal_points:
                        siggen.set_frequency(hz)
                        print(f"frequency set to {hz} Hz")
                        time.sleep(2.0)

                        pm.set_rate(pm.Rate.TriggerWithSettling)
                        (measured_dBm, status, range_, mode) = pm.read()
                        corrected_measured_dBm = measured_dBm * (cf / 100.)
                        assert status == pm.StatusOutput.MeasurementValid
                        assert mode == pm.ModeOutput.dBm
                        print(f"corrected read: {corrected_measured_dBm:6.3f} dBm, abs_error={abs(corrected_measured_dBm - power_level_dBm):6.3f} dB")
                        readings.append({'hz': hz,
                                         'cf': cf,
                                         'power_level_dBm': power_level_dBm,
                                         'measured_dBm': measured_dBm,
                                         'corrected_measured_dBm': corrected_measured_dBm})
        finally:
            siggen.set_output(False)

    df = pd.DataFrame(readings)
    print(df)

    yyyymmdd = datetime.datetime.today().strftime("%Y%m%d")
    csv_name = f"sensor_{sensor_info.model}_SN{sensor_info.serial}_{yyyymmdd}.csv"
    df.to_csv(csv_name)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
