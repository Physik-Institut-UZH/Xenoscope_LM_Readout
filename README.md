# Level Meter Readout

Minimal yet versatile code to set up and operate (through a Linux machine) the custom level meter readout board for the 
[Xenoscope](https://arxiv.org/abs/2105.13829) full-scale vertical demonstrator for the DARWIN observatory, or the 
level meter readout with a single smartec UTI evaluation board as used for the 
[MarmotX](https://www.physik.uzh.ch/en/groups/baudis/Research/Experiments-at-UZH.html) PMT testing facility. 
The current configuration for Xenoscope works with 3 short level meters (SLMs, channels 1-3) and a two-piece segmented 
long levelmeter (LLM, channels 4-5). Channel 6 is equipped with a reference capacitor for debugging. 
MarmotX accommodates a single level meter. All level meters allow for a capacitive liquid xenon level measurement 
in the respective setups. 

Prerequisites to run this code and set up the communication to the level meter readout devices via the 
Moxa UPort 1130 USB-to-Serial converter or the Tripp Lite U208-002-IND 2-Port RS-422/RS-485 USB to Serial FTDI Adapter 
(connecting to the custom multiple level meter readout board for Xenoscope), 
as well as in case of using the integrated FTDI chip on the smartec UTI evaluation board for MarmotX:

- Determine the port name using the `check_usb_ports.sh` script and provide appropriate permissions for that port, 
  e.g. with `sudo chmod 777 /dev/ttyUSB0`.

Additional prerequisites (Moxa UPort 1130 USB-to-Serial converter only):

- Install setserial on the machine (`sudo apt-get install -y setserial`).
- Install and load drivers for Moxa UPort 1100 series (simply run `./mxinstall` in unpacked drivers directory 
  obtained from [here](https://www.moxa.com/en/products/industrial-edge-connectivity/usb-to-serial-converters-usb-hubs/usb-to-serial-converters/uport-1100-series#resources)).
- Get the port's information, e.g. with `setserial -G /dev/ttyUSB0`, and set the interface to RS-422,
  e.g. with `setserial /dev/ttyUSB0 port 2`.

In order to perform special types of measurement for debugging and test purposes, refer to the respective 
functions in `setup_device.py`. For the standard continuous measurements (for all level meters at a standard 
cycle duration of ca. 3 s), run 

```
python3 run_measurement.py -v 1 -s 1 -n 10 -c 1
```

with the following optional arguments: 

- v: Set verbose output. Print measurement values to terminal.
- s: Save measurement values to csv file with entries: channel number, UNIX timestamp, capacitance in pF.
- n: Number of measurements taken and averaged per cycle and LM.
- c: Close port after measurement.

With a default of `c=False`, measurements can also be run without the necessity of 
initializing the port and board again after the first measurement by running 
in the Python console:

```
exec(open('run_measurement.py').read())
```

Any measurement can be regularly stopped by keyboard interrupt (`Ctrl`+`C`).

To plot the latest capacitance evolution for a quick check of the SLMs and LLMs (separate plots per LM type) 
run the `plotting.py` script. For more convenient plotting use the 
[Grafana interface](https://xenoscope-sc.physik.uzh.ch/grafana/dashboards) to visualize the data stored 
on the InfluxDB. 
