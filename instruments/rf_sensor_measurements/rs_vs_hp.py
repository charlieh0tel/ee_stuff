#!/usr/bin/env python

from pathlib import Path
import re
import sys

import matplotlib.pyplot as plt
import pandas as pd


_RE = r"^(sensor)_([a-zA-Z0-9]+)_(SN[a-zA-Z0-9]+)_([a-zA-Z0-9]+)_(\d{8})\.([a-zA-Z9-9]+)$"


def main(argv):
    globs = set()
    for csv in Path(".").glob("*.csv"):
        match = re.match(_RE, csv.name)
        if not match:
            continue
        model = match.group(2)
        sn = match.group(3)
        yyyymmdd = match.group(5)
        globs.add(f"sensor_{model}_{sn}_*_{yyyymmdd}.csv")

    for glob in globs:
        csvs = list(Path(".").glob(glob))
        dfs = []
        for csv in csvs:
            match = re.match(_RE, csv.name)
            siggen = match.group(4)
            df = pd.read_csv(csv)
            df['siggen'] = siggen
            dfs.append(df)
        combined_df = pd.concat(dfs, ignore_index=True)
        match = re.match(_RE, csv.name)
        model = match.group(2)
        sn = match.group(3)
        yyyymmdd = match.group(5)
        print(f"{model} {sn} {yyyymmdd}: {len(csvs)}")

        outname = f"{model}_{sn}_{yyyymmdd}"
        combined_df.to_parquet(f"{outname}.parquet")

        siggens = sorted(combined_df['siggen'].unique())
        siggen1 = siggens[0]
        siggen2 = siggens[1]

        assert len(siggens) == 2

        df_filtered = combined_df.dropna(
            subset=['hz', 'power_level_dBm',
                    'corrected_measured_dBm', 'siggen'])

        # Pivot the DataFrame to have 'hz' and 'power_level_dBm' as index
        # and 'siggen' as columns, with 'corrected_measured_dBm' as values.
        # This automatically aligns based on the index (hz and power_level_dBm)
        df_pivot = df_filtered.pivot_table(
            index=['hz', 'power_level_dBm'],
            columns='siggen',
            values='corrected_measured_dBm')

        df_pivot['difference_dB'] = df_pivot[siggen1] - df_pivot[siggen2]
        # df_pivot.iloc[:, 1] - df_pivot.iloc[:, 0])

        # Reset index to make 'hz' and 'power_level_dBm' columns again
        df_diff = df_pivot.reset_index()

        # Get unique power levels
        power_levels = df_diff['power_level_dBm'].unique()

        # Plotting
        plt.figure(figsize=(15, 10))

        for level in power_levels:
            df_subset = df_diff[df_diff['power_level_dBm'] == level]
            plt.plot(df_subset['hz'], df_subset['difference_dB'],
                     label=f'Power Level: {level} dBm', marker='x')

        plt.xscale('log')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel(f'({siggen1} - {siggen2}) [dB]')
        plt.suptitle(outname)
        plt.title(
            'Difference in Corrected Measured dBm vs. Frequency by Power Level')
        plt.legend(title='Power Level')
        plt.grid(True, which="both", ls="--", linewidth=0.5)

        plt.savefig(outname + "_siggen_compare.png")

        plt.show()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
