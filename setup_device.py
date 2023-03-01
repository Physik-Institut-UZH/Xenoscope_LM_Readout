"""
Set up communication to level meter readout device via

- Moxa UPort 1130 USB-to-Serial converter for custom multiple level meter readout board, or
- integrated FTDI chip on single level meter smartec UTI evaluation board.

Prerequisites:

- Determine port number using check_usb_ports.sh script and set appropriate rights for that port, e.g. with
  `sudo chmod 777 /dev/ttyUSB0`.

Prerequisites (Xenoscope level meter readout board only):

- Install setserial (`sudo apt-get install -y setserial`).
- Install and load drivers for Moxa UPort 1100 series (simply run `./mxinstall` in unpacked drivers directory).
- Get the port's information, e.g. with `setserial -G /dev/ttyUSB0`, and set interface to RS-422,
  e.g. with `setserial /dev/ttyUSB0 port 2`.
"""

import numpy as np
import serial
import subprocess
import time
from typing import Union, List


class LMReadout:
    """Set up communication to level meter readout device.

    Attributes:
        port: Port name string, usually '/dev/ttyUSB0'.
        name: Device name, 'moxa' (for custom multiple level meter readout board)
            or 'ftdi' (for single level meter smartec UTI evaluation board).
    """
    def __init__(self):
        # Find port
        self.port, self.name = self.find_port(name_options=('moxa', 'ftdi'))
        # Check standard
        if self.port == 'moxa':
            self.check_rs422(p=self.port)
        # Setup device
        self.ser = self.setup_device()
        # Print mode device
        self.get_mode()

    @staticmethod
    def find_port(name_options: tuple = ('moxa', 'ftdi')) -> tuple:
        """Find USB port with either Moxa UPort 1130 USB-to-Serial converter or FTDI FT230X Basic UART chip.

        Args:
            name_options: Tuple of strings contained in possible connection names
                as displayed by check_usb_ports.sh script. Default: ('moxa', 'ftdi').

        Returns:
            ports: Port name string, usually '/dev/ttyUSB0'.
            name: Device name string, 'moxa' or 'ftdi'.
        """
        # Run check_usb_ports.sh script to list ports.
        print('Finding port for level meter readout device.')
        ports = subprocess.run(['bash', 'check_usb_ports.sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ports = ports.stdout.decode().split('\n')
        # Find and select device and port name.
        ports_dict = {}
        for name in name_options:
            ports_dict[name] = [el for el in ports if name in el.lower()]
        if not np.any([bool(ports_dict.get(el)) for el in ports_dict]):
            raise ValueError('Found no ports that match {}.'.format(name_options))
        elif np.sum([len(ports_dict.get(el)) for el in ports_dict]) > 1:
            raise ValueError('Found multiple ports that match {}.'.format(name_options))
        else:
            name = [el for el in ports_dict if bool(ports_dict.get(el))][0]
            ports = ports_dict[name]
            ports = ports[0].split(' - ')[0]
            print(ports)
            if name != 'moxa':
                raise NotImplementedError('Only Xenoscope readout implemented so far.')  # TODO: implement MarmotX LM
        return ports, name

    @staticmethod
    def check_rs422(p: str):
        """Check whether port communication for Moxa is set to RS-422.

        Args:
            p: Port string as of find_port function.
        """
        print('Checking if {} is set to RS-422.'.format(p))
        port_setting = subprocess.run(['setserial', '-G', '/dev/ttyUSB0'],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        port_setting = port_setting.stdout.decode()
        if '0x0002' not in port_setting:
            raise OSError('{} does not seem to be set to RS-422.'.format(p))
        else:
            print('OK')

    def setup_device(self, echo: bool = False, verbose: bool = False, debug: bool = False, speed: str = 'f'):
        """
        Setup communication to level meter readout board.
        Inputs:
            - echo: Turn on/off command line echo.
              Default: False (i.e. echo off)
            - verbose: Turn on/off verbose output.
              Default: False (i.e. verbose output off)
            - debug: Turn on/off debug information.
              Default: False (i.e. debug information off)
            - speed: Set the measurement speed to fast ('f', ca. 100 samples/sec)
              or slow ('s', ca. 10 samples/sec).
              Default: 'f' (i.e. fast mode)
        Returns:
            - ser: serial.Serial(...)
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

    def print_lines(self):
        """
        Read returns level meter readout board and print as output.
        """
        read_raw_content = self.ser.readlines()
        for read_content_line in read_raw_content:
            # print(read_content_line)
            read_content_line = read_content_line.decode()
            print(read_content_line, end='')

    def help_board(self):
        """
        Print built-in help on level meter readout board.
        """
        print('\n########## Help info ##########')
        self.ser.write(b'help\n')  # "h" or "help"
        self.print_lines()
        print('####################\n')

    def about_board(self):
        """
        Print built-in information on level meter readout board.
        """
        self.ser.write(b'about\n')  # "about"
        self.print_lines()

    def get_mode(self):
        """
        Output state of settings level meter readout board.
        """
        print('Settings level meter readout board:')
        self.ser.write(b'getmode\n')  # "getmode"
        self.print_lines()

    def read_channel(self, channel: int = 1, n_readings: int = 10, mode: str = 'a'):
        """
        Take single channel measurement with level meter readout board.
        Inputs:
            - channel: Number channel to be read (integer from 1-6).
            - n_readings: Number of consecutive readings in this channel.
            - mode: Output single measurements (r) or averaged value (a).
        Returns:
            - read_raw_content: Capacitance value (or array of those for multiple readings) in pF.
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

    def read_channels(self, channels: Union[List, str] = 'a', n_readings: int = 10, mode: str = 'a'):
        """
        Take multiple channels measurement with level meter readout board.
        Inputs:
            - channels: List of channel numbers to be read (integer from 1-6) or string 'a' = all channels /
              'l' = LLMs only / 's' = SLMs only.
            - n_readings: Number of consecutive readings per channel.
            - mode: Output single measurements (r) or averaged value (a).
        Returns:
            - out: List of lists with channel numbers, UNIX timestamps, and capacitance values in pF.
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
