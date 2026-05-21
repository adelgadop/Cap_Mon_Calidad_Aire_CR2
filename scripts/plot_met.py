# conda activate monet
import monet
import monetio as mio
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotcmaq
import stats

met_modfile = ['../post/writesite_cmaq_d02_CR2_met_202409.csv']
obs_file = '../post/mirante_aug_sep_2024.pkl'
met_all, met_stats = plotcmaq.met_val(met_modfile,
                                      obsfile = pd.read_pickle(obs_file))

print(met_stats)

# Plot files
ylabels = {'tc': 'Temperature (°C)', 
           'rh': 'Relative\nHumidity (%)', 
           'ws': 'Wind Speed (m/s)', 
           'wd': 'Wind Direction (°)'}
met_list = list(ylabels.keys())
plotcmaq.met(met_all, ylabels, met_list, figsize =(10,8), savefig = '../figs/metplot.png')
plt.show()