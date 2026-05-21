
# conda activate monet
import plotcmaq
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import stats

files = ['../post/writesite_cmaq_d02_CR2_aq_202408.csv',
         '../post/writesite_cmaq_d02_CR2_aq_202409.csv']
stations = pd.read_csv('../namelists/stations_aq.csv')
names_stations = {code: name for code, name in zip(stations.code, stations.name)}
metfile = ['../post/writesite_cmaq_d02_CR2_met_202409.csv']
cmaq = plotcmaq.read_writesite(files, to_CO_ppm= True)
# local_date, code 'PM10', 'PM25_TOT', 'O3_UGM3', 'NO_UGM3', 'NO2_UGM3', 'CO', 'SO2_UGM3'
#cmaq['CO'] = cmaq['CO'] / 1000 # convert to ppm
cmaq.rename(columns={'PM25_TOT':'pm2_5', 'O3_UGM3':'o3', 'NO2_UGM3':'no2', 'CO':'co'}, inplace=True)

wrf = pd.read_pickle('../post/wrfchem_sp_aug_sep_2024.pkl')
# local_date, code,'PM2_5_DRY', 'o3', 'co', 'no', 'no2', 'so2',
wrf.rename(columns={'PM2_5_DRY':'pm2_5'}, inplace=True)

obs = pd.read_pickle('../post/obs_sp_aug_sep_2024.pkl')
# 'local_date', 'o3', 'no', 'no2', 'co', 'so2', 'tol', 'pm10', 'pm2_5',
# 'code', 'tc', 'rh', 'sr', 'ws', 'wd'

code = 99
units = ' ($\mu$g m$^{-3}$)'
labels = {'pm2_5': 'PM$_{2.5}$' + units, 'o3': 'O$_3$'+ units, 'co': 'CO (ppm)',
          'no': 'NO' + units, 'no2': 'NO$_2$' + units}

fig, ax = plt.subplot_mosaic([['pm2_5', 'o3'], ['co', 'no2']], figsize=(10, 6), 
                             sharex=True)
for pol in ['pm2_5', 'o3', 'co', 'no2']:
    (obs
    .loc[(obs.code == code) & (obs.local_date >= '2024-08-29') & (obs.local_date <= '2024-09-15'),:]
    .set_index('local_date')
    [pol].plot(ax=ax[pol], style='.k', label = 'CETESB'))

    (cmaq
    .loc[cmaq.code == code,:]
    .set_index('local_date')
    [pol].plot(ax=ax[pol], style='-', lw=2, color = '#03AED2',  alpha = .7, label = 'CMAQ'))

    (wrf
    .loc[wrf.code == code,:]
    .set_index('local_date')
    [pol].plot(ax=ax[pol], style='-', lw=2, color = '#FA6781', alpha = .7, label = 'WRF-Chem'))
    ax[pol].set_ylabel(labels[pol])
    ax[pol].set_xlabel('')
    ax[pol].spines['top'].set_visible(False)
    ax[pol].spines['right'].set_visible(False)
ax['pm2_5'].set_title(f'{names_stations.get(code, "Unknown Station")}', loc='left')
ax['co'].legend(fontsize=8, ncol=1)
fig.savefig('../figs/comparar_models.png', bbox_inches='tight', format='png')
plt.show()

# Statistics -------------------------------------------------------------------
wrf_obs_df = wrf.merge(obs, on = ['local_date', 'code'], suffixes=('_mod', '_obs'), how='inner')
cmaq_obs_df = cmaq.merge(obs, on = ['local_date', 'code'], suffixes=('_mod', '_obs'), how='inner')
pols = ['pm2_5', 'o3', 'co', 'no2']
# mod_dic = {'WRF-Chem': stats.aq_stats(wrf_obs_df, pols).round(2),
#            'CMAQ': stats.aq_stats(cmaq_obs_df, pols).round(2)}
# df_stats = pd.concat(mod_dic, axis=1)
# df_stats.index.name = 'statistics'
# df_stats
df = stats.aq_stats(cmaq_obs_df, pols, by_code = True)
#
print(df)