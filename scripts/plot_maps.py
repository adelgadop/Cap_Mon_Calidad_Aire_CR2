# conda activate monet
import monet
import monetio as mio
import matplotlib.pyplot as plt
import plotcmaq
import plotwrf
import pickle


# CMAQ -------------------------------------------------------------------------
# pathdir = '../data/cmaqout/'
# file = 'COMBINE_ACONC_v55_intel_CR2_BASEv01_20240*.nc'
# combine = mio.cmaq.open_mfdataset(pathdir + file)

# pol = 'PM2.5'
# plot_kws = dict(nqv = 5, 
#                 exag = 5, 
#                 vmin = 10,
#                 vmax = 40 if pol in ['PM2.5','pm2.5'] else 150, 
#                 levels = 15, 
#                 alpha = .6)

# plotcmaq.map(combine, stat='24h', pol= pol,
#              set_extent=[-47.1, -46.1, -24.1, -23.1], 
#              cmap='jet',
#              plot_kws=plot_kws, 
#              shapefiles = ['../data/geo_d02_roads.shp/edges.shp',
#                            '../figs/MunRM07.shp'],
#              pathsavefile=f'../figs/cmaq_{pol}_map.png')

# WRF-Chem ---------------------------------------------------------------------
with open("../data/wrfchemout/wrfchemout_join.pkl", "rb") as f:
    ds = pickle.load(f)
pol = 'o3'
plot_kws = dict(nqv = 5, exag = 5, vmin = 10, vmax = 50 if pol == 'pm2.5' else 150, 
                levels = 15, alpha = .6)

plotwrf.map(ds, pol=pol, stat='8h', cmap = 'jet', plot_kws=plot_kws,
            shapefiles= ['../data/geo_d02_roads.shp/edges.shp',
                         '../figs/MunRM07.shp'],
       set_extent=[-47.1, -46.1, -24.1, -23.1],
       savefig=f'../figs/wrfchem_{pol}_aug_sep2024.png')
