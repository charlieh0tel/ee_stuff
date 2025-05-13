#!/usr/bin/env python

import dataclasses
import datetime
import sys
import time

import matplotlib.pyplot as plt
import pandas as pd
import pyvisa

import rs_smb100a
import hp_436a
import hp_8662a


#DEFAULT_SIG_GEN_RESOURCE = "TCPIP::rssmb100a180609.local::INSTR"
DEFAULT_SIG_GEN_RESOURCE = "TCPIP::e5810a::gpib0,25::INSTR"
DEFAULT_POWER_METER_RESOURCE = "TCPIP::e5810a::gpib0,13::INSTR"


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

    readings = []
    #with rs_smb100a.RhodeSchwarzSMB100A(rm, sig_gen_resource) as siggen:
    with hp_8662a.HP8662A(sig_gen_resource) as siggen:
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
                    print("zeroing....")
                    pm.zero_meter()
                    siggen.set_power(power_level_dBm)
                    siggen.set_output(True)

                    for (hz, cf) in sensor_info.cal_points:
                        if hz > 2.560e9: continue

                        siggen.set_frequency(hz)
                        print(f"frequency set to {hz} Hz")
                        time.sleep(0.1)

                        try:
                            measured_dBm = pm.read_with_settling_dBm()
                        except TimeoutError:
                            print("timeout!")
                            continue
                        corrected_measured_dBm = measured_dBm * (cf / 100.)
                        print(f"power_level: {power_level_dBm} dBm, ", end="")
                        print(f"corrected: {corrected_measured_dBm:6.2f} dBm, ", end="")
                        abs_err_dB = abs(corrected_measured_dBm - power_level_dBm)
                        print(f"abs_error_dB: {abs_err_dB:4.2f} dB")
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
    output_basename = (f"sensor_{sensor_info.model}_"
                   f"SN{sensor_info.serial}_{yyyymmdd}")
    df.to_csv(output_basename + ".csv", index=False)
    
    # Plot.
    plt.figure(figsize=(10, 6))
    for level in df['power_level_dBm'].unique():
        level_df = df[df['power_level_dBm'] == level]
        plt.plot(level_df['hz'], level_df['corrected_measured_dBm'],
                 label=f'{level} dBm', marker='x')
    plt.xscale('log')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Corrected Measured Power (dBm)')
    plt.title(output_basename)
    plt.legend()
    plt.grid(True, which="both", ls="--", linewidth=0.5)
    plt.savefig(output_basename + ".png")
    plt.show()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
