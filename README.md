# Level Meter Readout

Minimal yet versatile code to set up and run the custom level meter readout board for the 
[Xenoscope](https://arxiv.org/abs/2105.13829) full-scale vertical demonstrator for the DARWIN observatory 
on a Linux machine. 
The current configuration works with 3 short level meters (SLMs, channels 1-3) and a two-piece segmented 
long levelmeter (LLM, channels 4-5). Channel 6 is equipped with a reference capacitor for debugging. 

Prerequisites to run this code and set up communication to the level meter readout board via a 
Moxa UPort 1130 USB-to-Serial converter:

- Install setserial on the machine (`sudo apt-get install -y setserial`).
- Install and load drivers for Moxa UPort 1100 series (simply run `./mxinstall` in unpacked drivers directory 
  obtained from [here](https://www.moxa.com/en/products/industrial-edge-connectivity/usb-to-serial-converters-usb-hubs/usb-to-serial-converters/uport-1100-series#resources)).
- Determine the port number using the `check_usb_ports.sh` script and provide appropriate permissions for that port, 
  e.g. with `sudo chmod 777 /dev/ttyUSB0`.
- Get the port's information, e.g. with `setserial -G /dev/ttyUSB0`, and set the interface to RS-422,
  e.g. with `setserial /dev/ttyUSB0 port 2`.

In order to perform special types of measurement for debugging and test purposes, refer to the respective 
functions in `setup_device.py`. For the standard continuous measurements (for all five level meters at a standard 
cycle duration of ca. 3 s), run 

```
python3 run_measurement.py -v 1 -s 1 -n 10 -c 1
```

with the following arguments: 

- v: Set verbose output. Print measurement values to terminal.
- s: Save measurement values to csv.
- n: Number of measurements taken and averaged per cycle and LM.
- c: Close port after measurement.

With a default of `c=False`, measurements can also be run without the necessity of 
initializing the port and board again after the first measurement by running 
in the Python console:
```
exec(open('run_measurement.py').read())
```

Any measurement can be regularly stopped by keyboard interrupt (`Ctrl`+`C`).
