"""
Set up communication to level meter readout device via

- Moxa UPort 1130 USB-to-Serial converter for custom multiple level meter readout board (-> Xenoscope), or
- Tripp Lite U208-002-IND 2-Port RS-422/RS-485 USB to Serial FTDI Adapter with COM Retention (USB-B to DB9 F/M) as
  alternative for the custom multiple level meter readout board (-> Xenoscope), or
- integrated FTDI chip on single level meter smartec UTI evaluation board (-> MarmotX).

Prerequisites:

- Determine port number using check_usb_ports.sh script and set appropriate rights for that port, e.g. with
  `sudo chmod 777 /dev/ttyUSB0`.

Prerequisites (Moxa UPort 1130 USB-to-Serial converter only):

- Install setserial (`sudo apt-get install -y setserial`).
- Install and load drivers for Moxa UPort 1100 series (simply run `./mxinstall` in unpacked drivers directory).
- Get the port's information, e.g. with `setserial -G /dev/ttyUSB0`, and set interface to RS-422,
  e.g. with `setserial /dev/ttyUSB0 port 2`.
"""

import numpy as np
import serial
import subprocess
import time
import warnings
from typing import Union, List


class LMReadout:
    """Set up communication to level meter readout device.

    Attributes:
        port: Port name string, usually '/dev/ttyUSB0'.
        name: Device name, 'moxa' / 'ftdi_dual' (for custom multiple level meter readout board)
            or 'ftdi_ft230x' (for single level meter smartec UTI evaluation board).
    """
    def __init__(self):
        # Find port
        self.port, self.name = self.find_port(name_options=('moxa', 'ftdi_ft230x', 'ftdi_dual'))
        if self.name == 'moxa':
            # Check standard
            self.check_rs422(p=self.port)
            # Setup device
            self.ser = self.setup_readout_board()
            # Print mode device
            self.get_mode()
        elif self.name == 'ftdi_ft230x':
            # Setup device
            self.ser = self.setup_smartec_board()
        if self.name == 'ftdi_dual':
            # Setup device
            self.ser = self.setup_readout_board()
            # Print mode device
            self.get_mode()
        if self.name not in ('moxa', 'ftdi_ft230x', 'ftdi_dual'):
            raise NotImplementedError('Name {} not a valid option, select from '
                                      'implemented (moxa, ftdi_ft230x, ftdi_dual).'.format(self.name))

    @staticmethod
    def find_port(name_options: tuple = ('moxa', 'ftdi_ft230x', 'ftdi_dual')) -> tuple:
        """Find USB port with either Moxa UPort 1130 USB-to-Serial converter or FTDI FT230X Basic UART chip.

        Args:
            name_options: Tuple of strings contained in possible connection names
                as displayed by check_usb_ports.sh script. Default: ('moxa', 'ftdi_ft230x', 'ftdi_dual').

        Returns:
            ports: Port name string, usually '/dev/ttyUSB0'.
            name: Device name string, 'moxa', 'ftdi_ft230x', or 'ftdi_dual'.
        """
        # Run check_usb_ports.sh script to list ports.
        print('Finding port for level meter readout device.')
        ports = subprocess.run(['bash', 'check_usb_ports.sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ports = ports.stdout.decode().split('\n')
        # Find and select device and port name.
        ports_dict = {}
        for name in name_options:
            ports_dict[name] = [el for el in ports if name in el.lower()]
        found_device_types = [k for k, v in ports_dict.items() if bool(v)]
        if not bool(found_device_types):
            raise ValueError('Found no ports that match {}.'.format(name_options))
        elif (np.sum([len(ports_dict.get(el)) for el in ports_dict]) > 1) and \
                not ((len(found_device_types) == 1) and (found_device_types[0] == 'ftdi_dual')):
            raise ValueError('Found multiple ports that match {}: {}.'.format(name_options, ports_dict))
        else:
            if found_device_types[0] == 'ftdi_dual':
                print('Connected to 2-Port RS-422/RS-485 USB to Serial FTDI Adapter. Will use PORT 1.')
            name = [el for el in ports_dict if bool(ports_dict.get(el))][0]
            ports = ports_dict[name]
            ports = np.sort(ports)[0].split(' - ')[0]
            print(ports)
            if name not in ('moxa', 'ftdi_ft230x', 'ftdi_dual'):
                raise NotImplementedError('Name {} not a valid option, select from '
                                          'implemented (moxa, ftdi_ft230x, ftdi_dual).'.format(name))
        return ports, name

    @staticmethod
    def check_rs422(p: str):
        """Check whether port communication for Moxa is set to RS-422.

        Args:
            p: Port string as of find_port function.
        """
        print('Checking if {} is set to RS-422.'.format(p))
        port_setting = subprocess.run(['setserial', '-G', p],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        port_setting = port_setting.stdout.decode()
        if '0x0002' not in port_setting:
            raise OSError('{} does not seem to be set to RS-422.'.format(p))
        else:
            print('OK')

    def setup_readout_board(self, echo: bool = False, verbose: bool = False, debug: bool = False, speed: str = 'f'):
        """Setup communication to level meter readout board.

        Args:
            echo: Turn on/off command line echo.
                Default: False (i.e. echo off)
            verbose: Turn on/off verbose output.
                Default: False (i.e. verbose output off)
            debug: Turn on/off debug information.
                Default: False (i.e. debug information off)
            speed: Set the measurement speed to fast ('f', ca. 100 samples/sec)
                or slow ('s', ca. 10 samples/sec).
                Default: 'f' (i.e. fast mode)
        Returns:
            ser: Serial object.
        """
        print('Setting serial port properties. ')
        ser = serial.Serial(
            port=self.port,
            baudrate=115200,  # 115200 baud
            parity=serial.PARITY_NONE,  # no parity
            stopbits=serial.STOPBITS_ONE,  # one stop bit
            bytesize=serial.EIGHTBITS,  # 8 data bit
            timeout=2)
        print('Selected port: {}'.format(ser.name))
        if not ser.is_open:
            raise OSError('Selected serial port ' + self.port + ' seems to not be open!')

        if echo:
            ser.write(b'echo 1\n')
        else:
            ser.write(b'echo 0\n')

        if verbose:
            ser.write(b'verbose 1\n')
        else:
            ser.write(b'verbose 0\n')

        if debug:
            ser.write(b'debug 1\n')
        else:
            ser.write(b'debug 0\n')

        if speed in ['f', 'fast']:
            ser.write(b'f\n')
        elif speed in ['s', 'slow']:
            ser.write(b's\n')
        else:
            raise ValueError('Argument speed can only take options fast or slow.')

        read_raw_content = ser.readlines()
        for read_content_line in read_raw_content:
            # print(read_content_line)
            read_content_line = read_content_line.decode()
            print(read_content_line, end='')

        return ser

    def setup_smartec_board(self, mode_sf: str = b's', mode: str = b'4'):
        """Setup communication to UTI evaluation board and set wanted mode.

        Args:
            mode_sf: Fast (b'f', 10 ms cycle) or slow (b's', 100 ms cycle) mode.
                Default: b's'
            mode: Measurement mode (0, 1, 2, 4).
                For now only allow mode 4 (1 unknown capacitor Cda + 1 reference capacitor Cca,
                variable range (<300pF)), otherwise will need to adjust code.
                Default: b'4'
        Returns:
            ser: Serial object.
        """
        if (mode_sf != b's') & (mode_sf != b'f'):
            mode_sf = b's'
            print('Please select a valid option for mode_sf. Falling back to slow mode for now.')
        if mode != b'4':
            mode = b'4'
            print('Please select a valid option for mode. Falling back to mode 4 for now.')

        print('Setting serial port properties. ')
        ser = serial.Serial(
            port=self.port,
            baudrate=9600,  # 9600 baud
            parity=serial.PARITY_NONE,  # no parity
            stopbits=serial.STOPBITS_ONE,  # one stop bit
            bytesize=serial.EIGHTBITS,  # 8 data bit
            timeout=2)
        print('Selected port: {}'.format(ser.name))
        if not ser.is_open:
            raise OSError('Selected serial port ' + self.port + ' seems to not be open!')

        # Once the communication between the microcontroller and the PC is
        # established start with sending an @ sign to the board in order to set the
        # correct communication speed
        print('Setting communication speed for board.')
        ser.write(b'@')

        # Mode 4 - 3 Capacitors, variable range to 300 pF
        if mode == b'4':
            print('Setting mode 4 (1 unknown capacitor + 1 reference capacitor variable range (<300pF)).')
        else:
            print('Setting non-default mode {}. Is this intended?'.format(mode))
        ser.write(mode)

        # Set fast or slow mode
        if mode_sf == b's':
            print('Setting slow mode (100 ms cycle).')
        elif mode_sf == b'f':
            print('Setting fast mode (10 ms cycle).')
        else:
            raise ValueError('Trying to set mode_sf to an invalid value.')
        ser.write(mode_sf)

        return ser

    def print_lines(self):
        """Read returns level meter readout board and print as output.
        """
        read_raw_content = self.ser.readlines()
        for read_content_line in read_raw_content:
            # print(read_content_line)
            read_content_line = read_content_line.decode()
            print(read_content_line, end='')

    def help_board(self):
        """Print built-in help on level meter readout board.
        """
        print('\n########## Help info ##########')
        if self.name in ('moxa', 'ftdi_dual'):
            self.ser.write(b'help\n')  # "h" or "help"
        elif self.name == 'ftdi_ft230x':
            self.ser.write(b'H')  # “H”, “h” or “?”
        else:
            raise NotImplementedError('Method not supported for used device {}.'.format(self.name))
        self.print_lines()
        print('####################\n')

    def about_board(self):
        """Print built-in information on level meter readout board.
        """
        if self.name in ('moxa', 'ftdi_dual'):
            self.ser.write(b'about\n')  # "about"
        else:
            raise NotImplementedError('Method not supported for used device {}.'.format(self.name))
        self.print_lines()

    def get_mode(self):
        """Output state of settings level meter readout board.
        """
        if self.name in ('moxa', 'ftdi_dual'):
            print('Settings level meter readout board:')
            self.ser.write(b'getmode\n')  # "getmode"
        else:
            raise NotImplementedError('Method not supported for used device {}.'.format(self.name))
        self.print_lines()

    def single_test_measurement_smartec_board(self):
        """Perform single test measurement for single level meter smartec UTI evaluation board.
        May be slow due to the use of `readlines()` instead of `readline()`.
        Meant for demonstration and debugging purposes.
        """
        self.ser.write(b'm')

        read_raw_content = self.ser.readlines()
        if len(read_raw_content) < 1:
            raise ValueError('The microcontroller does not have any data that can be read.')
        elif len(read_raw_content) > 1:
            warnings.warn('The microcontroller provides multiple lines of data to be read:')
            for read_content_line in read_raw_content:
                print(read_content_line)
            print('Only selecting last line.')
            read_raw_content = read_raw_content[-1]
        else:
            read_raw_content = read_raw_content[0]

        # read_raw_content = read_raw_content.decode('ascii')
        read_raw_content = read_raw_content.split()
        print('Output (hex):')
        print(read_raw_content)

        read_conv_content = [int(el, 16) for el in read_raw_content]
        print('Converted output (dec):')
        print(str(read_conv_content) + ' = [Tba, Tca, Tda]')

    def single_test_measurement_readout_board(self, channel: int = 1, n_readings: int = 10, mode: str = 'a'):
        """Take single channel test measurement with level meter readout board.
        Meant for demonstration and debugging purposes.

        Args:
            channel: Number channel to be read (integer from 1-6).
            n_readings: Number of consecutive readings in this channel.
            mode: Output single measurements (r) or averaged value (a).
        Returns:
            read_raw_content: Capacitance value (or array of those for multiple readings) in pF.
        """
        if channel not in range(1, 6+1):
            raise ValueError('channel must be an integer between 1 and 6.')
        if not type(n_readings) is int:
            raise ValueError('n_readings must be an integer.')
        if mode not in ['r', 'a']:
            raise ValueError('mode must be a or r.')

        self.ser.write(f'{mode} {channel} {n_readings}\n'.encode())
        read_raw_content = self.ser.readlines()
        if len(read_raw_content) < 1:
            raise ValueError("The level meter readout board doesn't have any data that can be read.")
        read_raw_content = np.array([el.decode().translate({ord(i): None for i in ' \r\n'})
                                     for el in read_raw_content]).astype(float)

        if len(read_raw_content) == 1:
            read_raw_content = read_raw_content[0]

        return read_raw_content

    def measure_capacitance_smartec_board(self, cref: float = 100, n_iterations_per_loop: int = 5,
                                          verbosity: int = 0) -> np.ndarray:
        """Conduct `n_iterations_per_loop` consecutive measurement cycles 
        and return average calculated capacitance.
        
        Args:
            cref: reference capacitance (Cca) in pF.
                Default: 150
            n_iterations_per_loop: Capacitance measurement cycles conducted for 
                averaged output value in one call of measure_capacitance. 
                Default: 5 (to naively reduce statistical uncertainty by factor of 2)
            verbosity: Verbosity (0-3). 
                Default: 0 (nothing gets printed)
        Outputs: 
            - cx: Derived unknown capacitance (Cda) in pF.
        """
        if cref < 0:
            raise ValueError("Invalid value for cref.")
        if n_iterations_per_loop < 1:
            raise ValueError("Invalid value for n_iterations_per_loop.")

        time.sleep(0.15)
        for i in range(n_iterations_per_loop):
            self.ser.write(b'm')  # do single measurement
            # Sleep for 0.15 seconds as in slow mode the duration of one 
            # complete cycle of the output signal is about 100 ms.
            time.sleep(0.15)

        read_raw_content = self.ser.readlines()  # read all output lines from board
        if len(read_raw_content) < 1:
            raise ValueError("The microcontroller doesn't have any data that can be read.")
        read_raw_content = np.array([el.split() for el in read_raw_content])  # convert to array

        if verbosity >= 3:
            print('Measured periods (hex):')
            for el in read_raw_content:
                print(el)

        # Convert output periods from hex to dec
        periods_list = np.ones_like(read_raw_content, dtype=int)
        for i in range(len(read_raw_content)):
            # print(read_raw_content[i])
            for j in range(3):
                periods_list[i, j] = int(read_raw_content[i, j], 16)

        if verbosity >= 3:
            print('Converted periods (dec) [Tba, Tca, Tda]:')
            for el in periods_list:
                print(el)

        tba = periods_list[:, 0]
        tca = periods_list[:, 1]
        tda = periods_list[:, 2]

        # Calculate ratio Cx/Cref
        m = (tda - tba) / (tca - tba)
        if verbosity >= 2:
            print('Ratio Cx/Cref:')
            print(m)

        # Calculate unknown capacitance and return mean value
        cx = m * cref
        if verbosity >= 2:
            print('Individual cx values (for Cref = ' + str(cref) + ' pF):')
            print(cx)
            print('Average: ')
        cx = np.mean(cx)
        if verbosity >= 1:
            print(cx)

        return cx

    def read_channel_smartec_board(self, n_readings: int = 5) -> list:
        """Take continuous multiple channels measurement with smartec UTI evaluation board.

        Args:
            n_readings: Number of averaged consecutive readings.

        Returns:
            out: List with channel number (set to -1 to disable in plotting),
                UNIX timestamps, and capacitance values in pF.
        """
        if not type(n_readings) is int:
            raise ValueError('n_readings must be an integer.')

        timestamp = time.time()
        capacitance = self.measure_capacitance_smartec_board(n_iterations_per_loop=n_readings)
        out = [[-1], [timestamp], [capacitance]]
        out = [list(el) for el in zip(*out)]  # Transpose list

        return out

    def read_channels_readout_board(self, channels: Union[List, str] = 'a', n_readings: int = 10,
                                    mode: str = 'a') -> list:
        """Take continuous multiple channels measurement with custom multiple level meter readout board.

        Args:
            channels: List of channel numbers to be read (integer from 1-6) or string 'a' = all channels /
                'l' = LLMs only / 's' = SLMs only.
            n_readings: Number of consecutive readings per channel.
            mode: Output single measurements (r) or averaged value (a).
        Returns:
            out: List of lists with channel numbers, UNIX timestamps, and capacitance values in pF.
        """
        if type(channels) == list:
            for i in channels:
                if i not in range(1, 6 + 1):
                    raise ValueError('Channel numbers must be integers between 1 and 6.')
            ch = channels
        elif type(channels) == str:
            if channels == 'a':
                ch = [1, 2, 3, 4, 5]
            elif channels == 's':
                ch = [1, 2, 3]
            elif channels == 'l':
                ch = [4, 5]
            else:
                raise ValueError('Invalid value for channels.')
        else:
            raise ValueError('Invalid value for channels.')

        if not type(n_readings) is int:
            raise ValueError('n_readings must be an integer.')
        if mode not in ['r', 'a']:
            raise ValueError('mode must be a or r.')

        timestamps = np.zeros(len(ch))
        for i, channel in enumerate(ch):
            self.ser.write(f'{mode} {channel} {n_readings}\n'.encode())
            timestamps[i] = time.time()
            time.sleep(0.2)
        read_raw_content = self.ser.readlines()
        if len(read_raw_content) < 1:
            raise ValueError("The level meter readout board doesn't have any data that can be read.")
        read_raw_content = np.array([el.decode().translate({ord(i): None for i in ' \r\n'})
                                     for el in read_raw_content]).astype(float)

        out = [ch, timestamps, read_raw_content]
        out = [list(el) for el in zip(*out)]  # Transpose list

        return out
