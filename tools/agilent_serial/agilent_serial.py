#!/usr/bin/env python3

import sys
import csv


def main(argv):
    path = argv[1]
    with open(path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        rx_buffer = []
        tx_buffer = []

        def flush_buffers():
            nonlocal rx_buffer, tx_buffer
            if rx_buffer:
                print(f"RX: {' '.join(rx_buffer)}")
                rx_buffer = []
            if tx_buffer:
                print(f"TX: {' '.join(tx_buffer)}")
                tx_buffer = []

        for row in reader:
            rx_val = row.get('Rx', '').strip() or None
            tx_val = row.get('Tx', '').strip() or None
            time_val = row.get('Time', 'N/A').strip()

            if rx_val and tx_val:
                flush_buffers()
                print(f"BOTH at {time_val}: Rx={rx_val}, Tx={tx_val}")
            elif rx_val:
                if tx_buffer:
                    flush_buffers()
                rx_buffer.append(rx_val)
            elif tx_val:
                if rx_buffer:
                    flush_buffers()
                tx_buffer.append(tx_val)
            else:
                flush_buffers()
        flush_buffers()
            
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
