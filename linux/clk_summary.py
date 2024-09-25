import sys
from dataclasses import dataclass
import itertools
import textwrap

@dataclass
class Clock:
    name: str
    enable_count: int
    prepare_count: int
    protect_count: int
    rate: int
    accuracy: int
    phase: int
    duty_cycle: float
    hardware_enabled: bool

    @classmethod
    def parse(cls, line):
        parts = line.split()
        return cls(parts[0],             # name
                   int(parts[1]),        # enable_count
                   int(parts[2]),        # prepare_count
                   int(parts[3]),        # protect_count
                   int(parts[4]),        # rate
                   int(parts[5]),        # accuracy
                   int(parts[6]),        # phase
                   float(parts[7])/1e5,  # duty_cycle
                   parts[8] == 'Y'       # hardware_enable
                   )
    
    @classmethod
    def load_summary(cls, path):
        clocks = []
        with open(path) as f:
            # Header is three lines
            for _ in range(3):
                f.readline()
            for line in f:
                clocks.append(cls.parse(line))
        return clocks


def main(argv):
    assert 1 <= len(argv) <= 2
    clk_summary_path = argv[1] if len(argv) == 2 else "clk_summary"
    all_clocks = Clock.load_summary(clk_summary_path)
    active_clocks = itertools.filterfalse(lambda c: not c.hardware_enabled, all_clocks)
    active_clocks_sorted_by_rate = sorted(active_clocks, key=lambda c: c.rate)

    for k, g in itertools.groupby(active_clocks_sorted_by_rate,
                                  lambda c: c.rate):
        print(f"{k / 1e6} MHz")
        print(f"  (2x={2 * k / 1e6} MHz, 3x={3 * k / 1e6} MHz, 4x={4 * k / 1e6} MHz, 5x={5 * k / 1e6} MHz)")
        names = ", ".join(map(lambda c: c.name, g))
        print(textwrap.fill(names, initial_indent="  ", subsequent_indent="  "))
        print()

if __name__ == "__main__":
    main(sys.argv)
