"""
Plot latest level evolution.
"""

# Imports
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import os
import glob
import re
# Use custom plot design
plt.style.use(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'custom_style.mplstyle'))
# Set plot output
save_plots = True
show_plots = False

# Set input and output directories
data_path = './outputs/'
if not os.path.exists('./plots/'):
    os.makedirs('./plots/')
save_dir = './plots/'

# Select latest file
available_files = glob.glob(data_path+'levelmeters*')
available_dates = [re.findall(r'\d+', el) for el in available_files]
latest_date = max([int(el[0]) for el in available_dates])
filename = 'levelmeters_{}.csv'.format(latest_date)

# Load data
df = pd.read_csv(data_path+filename, header=None, names=['channel', 'timestamp', 'capacitance'])
# Convert UNIX time stamp to datetime for Central European Time
df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', utc=True).map(lambda x: x.tz_convert('Europe/Berlin'))
# Channel to level meter mapping dictionary for plot labels
names_dict = {'1': 'SLM 1', '2': 'SLM 2', '3': 'SLM 3',
              '4': 'LLM (upper)', '5': 'LLM (lower)', '6': 'Reference 100 pF'}


def plot_capacitances(channels: list, save_name='test'):
    """Plot capacitance evolution for selected channels.

    Args:
        channels: List of channel numbers to plot.
        save_name: Save name plots.
    """
    fig = plt.figure()
    for channel in channels:
        plt.plot(df[df.channel == int(channel)].datetime, df[df.channel == int(channel)].capacitance,
                 label=names_dict[str(channel)])
    plt.xlabel('Time')
    plt.ylabel('Capacitance [pF]')
    fig.autofmt_xdate()
    legend = plt.legend(loc=2, bbox_to_anchor=(1.005, 1.023))
    legend.get_frame().set_linewidth(matplotlib.rcParams['axes.linewidth'])
    if save_plots:
        plt.savefig(os.path.join(save_dir, save_name + '.png'))
        plt.savefig(os.path.join(save_dir, save_name + '.pdf'))
    if show_plots:
        plt.show()
    else:
        plt.close()


# Short level meters
plot_capacitances(channels=[1, 2, 3], save_name='SLMs')
# Long level meters
plot_capacitances(channels=[4, 5], save_name='LLMs')
