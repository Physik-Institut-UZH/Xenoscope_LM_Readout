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


class Plotting:
    """Plot the latest readings of selected level meters.

    Attributes:
        save_plots: Save output plot of the latest level evolution.
        show_plots: Display output plot of the latest level evolution.
        data_path: Input data directory.
        save_dir: Plot output directory.
        df: Dataframe with the latest capacitance values.
        names_dict: Channel to level meter mapping dictionary for plot labels.
    """
    def __init__(self, save_plots: bool = True, show_plots: bool = False,
                 data_path: str = './outputs/', save_dir: str = './plots/'):
        # Set plot output
        self.save_plots = save_plots
        self.show_plots = show_plots
        # Set input and output directories
        self.data_path = data_path
        self.save_dir = save_dir

        # Select latest file
        available_files = glob.glob(self.data_path+'levelmeters*')
        available_dates = [re.findall(r'\d+', el) for el in available_files]
        latest_date = max([int(el[0]) for el in available_dates])
        filename = 'levelmeters_{}.csv'.format(latest_date)

        # Load data
        self.df = pd.read_csv(self.data_path+filename, header=None, names=['channel', 'timestamp', 'capacitance'])
        # Convert UNIX time stamp to datetime for Central European Time
        self.df['datetime'] = pd.to_datetime(self.df['timestamp'], unit='s',
                                             utc=True).map(lambda x: x.tz_convert('Europe/Berlin'))
        # Channel to level meter mapping dictionary for plot labels
        self.names_dict = {'1': 'SLM 1', '2': 'SLM 2', '3': 'SLM 3',
                           '4': 'LLM (upper)', '5': 'LLM (lower)', '6': 'Reference 100 pF'}

    def plot_capacitances(self, channels: list, save_name='test'):
        """Plot capacitance evolution for selected channels.

        Args:
            channels: List of channel numbers to plot.
            save_name: Save name plots.
        """
        fig = plt.figure()
        for channel in channels:
            plt.plot(self.df[self.df.channel == int(channel)].datetime,
                     self.df[self.df.channel == int(channel)].capacitance,
                     label=self.names_dict[str(channel)])
        plt.xlabel('Time')
        plt.ylabel('Capacitance [pF]')
        fig.autofmt_xdate()
        legend = plt.legend(loc=2, bbox_to_anchor=(1.005, 1.023))
        legend.get_frame().set_linewidth(matplotlib.rcParams['axes.linewidth'])
        if self.save_plots:
            plt.savefig(os.path.join(self.save_dir, save_name + '.png'))
            plt.savefig(os.path.join(self.save_dir, save_name + '.pdf'))
        if self.show_plots:
            plt.show()
        else:
            plt.close()


if __name__ == "__main__":
    plotting = Plotting(save_plots=True, show_plots=False, data_path='./outputs/', save_dir='./plots/')
    # Short level meters
    plotting.plot_capacitances(channels=[1, 2, 3], save_name='SLMs')
    # Long level meters
    plotting.plot_capacitances(channels=[4, 5], save_name='LLMs')
