"""
Script to run continuous measurements with custom multiple level meter readout board or
single level meter smartec UTI evaluation board.
Press 'Ctrl'+'C' (KeyboardInterrupt) to stop acquisition.
"""

import numpy as np
import time
import re
import csv
import os
import argparse
from setup_device import LMReadout

parser = argparse.ArgumentParser(
    description=('Script to run continuous measurements with level meter readout board. '
                 'Press Ctrl+C (KeyboardInterrupt) to stop acquisition.')
)
parser.add_argument('-v', '--verbose',
                    help='Set verbose output. Print measurement values to terminal.',
                    type=bool,
                    default=True)
parser.add_argument('-s', '--save',
                    help='Save measurement values to csv.',
                    type=bool,
                    default=True)
parser.add_argument('-n', '--nmeasurements',
                    help='Number of measurements taken and averaged per cycle and LM.',
                    type=int,
                    default=10)
parser.add_argument('-c', '--close',
                    help='Close port after measurement.',
                    type=bool,
                    default=False)
args = parser.parse_args()

verbose = args.verbose
save_to_csv = args.save
n_readings = args.nmeasurements

print('Checking config level meter readout...')
try:
    # Check if serial port open and properly configured.
    if device.name in ('moxa', 'ftdi_dual'):
        device.ser.write(b'getmode\n')
        read_raw_content = device.ser.readlines()
        read_raw_content = np.array([el.decode().translate({ord(i): None for i in ' \r\n'}) for el in read_raw_content])
        # Verify that level meter readout board configured as desired.
        if read_raw_content.tolist() != ['Sf', 'V0', 'E0', 'D0']:
            raise ValueError('Level meter readout not set up yet.')
        print('OK')
    elif device.name == 'ftdi_ft230x':
        device.single_test_measurement_smartec_board()
        print('OK')
except Exception:
    device = LMReadout()

if device.name in ('moxa', 'ftdi_dual'):
    print('\n####################\n')
    channels = input('Type the channel numbers to read OR type "a" to read all channels OR\n'
                     'type "l" to read only LLMs OR type "s" to read only SLMs:')
    channels = channels.strip('\"')
    channels = channels.strip('\'')
    channels = channels.lower()
    if channels not in ['a', 's', 'l']:
        channels = ' '.join(channels)
        channels = re.findall(r'\d+', channels)
        channels = [int(el) for el in channels]
    if type(channels) not in [list, str]:
        raise TypeError('Unexpected input for channels.')

print('\n####################\n')
print('Starting measurement.\n')
print('Channel, UNIX Time Stamp, Capacitance [pf]')
k = False
if save_to_csv:
    it = 0
    max_it = 2000
    if not os.path.exists('./outputs/'):
        os.makedirs('./outputs/')
    filename = './outputs/levelmeters_{}.csv'.format(int(time.time()))

while k is False:
    try:
        if device.name in ('moxa', 'ftdi_dual'):
            out = device.read_channels_readout_board(channels=channels, n_readings=n_readings, mode='a')
        elif device.name == 'ftdi_ft230x':
            out = device.read_channel_smartec_board(n_readings=n_readings)
        if verbose:
            print(*out, sep='\n')
        if save_to_csv:
            if it % max_it == 0:
                filename = './outputs/levelmeters_{}.csv'.format(int(time.time()))
            with open(filename, 'a+', newline='') as f:
                write = csv.writer(f)
                write.writerows(out)
            it += 1
    except KeyboardInterrupt:
        print('\nDone.')
        k = True
        if args.close:
            device.ser.close()
            print('Closing port {}.'.format(device.ser.name))
