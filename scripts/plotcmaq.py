# conda activate monet in MacBook Pro
import pandas as pd
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.io.shapereader import natural_earth, Reader
import matplotlib.pyplot as plt
import xarray as xr
import monet
import monetio as mio
import typing
from typing import Union, Any, Optional, Tuple, List
from windrose import WindroseAxes, plot_windrose
import seaborn as sns
from stats import met_stats

# Reading Writesite-CMAQ output file --------------------------------------------------------------------------------
def read_writesite(files: list[str], 
                   tz_local: str = 'America/Sao_Paulo',
                   to_CO_ppm: bool = False) -> pd.DataFrame:
    print('Reading Writesite-CMAQ output file...')
    
    lista = []
    for filename in sorted(files):
        df = pd.read_csv(filename, skiprows=5, na_values = 'm' ).loc[1::, :]
        lista.append(df)
        
    all_df = pd.concat(lista, axis=0, ignore_index=True)
    all_df['local_time'] = [f"{date} {Time}" for date, 
                            Time in zip(all_df['date'], all_df['Time'])]
    all_df.drop(['column','row','longitude','latitude','date', 'Time'], 
                axis=1, inplace=True)
    all_df['local_date'] = pd.to_datetime(all_df['local_time'], 
                                          format='%Y-%m-%d %H:00:00', 
                                          utc = False).dt.tz_localize(tz_local)
    all_df.drop('local_time', axis=1, inplace=True)
    object_cols = all_df.select_dtypes(include=['object']).columns
    all_df[object_cols] = all_df[object_cols].astype(float)
    all_df.dropna(inplace=True)
    all_df.rename(columns={'siteid':'code'}, inplace=True)
    
    if to_CO_ppm == True:
        print(f'Assuming CO units in ppbV, converting to ppmV...')
        all_df['CO'] *= 1/1000 # to ppmV
        
    return all_df

def met_val(modfiles: list[str], obsfile: pd.DataFrame = None,
                 tz_local: str = 'America/Sao_Paulo') -> pd.DataFrame:
    '''
    Model performance evaluation for meteorological parameters,
    according to Emery (2001), Reboredo et al (2015), Monk et al (2019).
    '''
    mod = read_writesite(modfiles, tz_local=tz_local, to_CO_ppm=False)
    mod['tc'] = mod.SFC_TMP - 273.15
    mod.rename(columns={'WSPD10':'ws', 'WDIR10':'wd', 'RH':'rh'}, inplace=True)
    obs = obsfile.copy()
    
    met_all = mod.set_index('local_date').merge(obs,
                                  left_index=True, 
                                  right_index=True, suffixes=('_mod', '_obs'))

    df_stats = met_stats(met_all, mets=['tc','rh','ws', 'wd']).round(2).T
    return  met_all, df_stats
    
def met(met_all: pd.DataFrame, ylabels: dict, met_list: list, 
        labels: list = ['Observed', 'Modeled'],
        title: str = 'Mirante A701 São Paulo',
        color:  str ='#03AED2',
        figsize: tuple = (10, 6), savefig: Optional[str] = None) -> plt.Figure:
    print('Suffixes must be _obs and _mod for observed and modeled data, respectively.')
    
    met_list = list(ylabels.keys())
    fig, ax = plt.subplot_mosaic([['wr_obs', 'wr_mod'],
                                #   ['.','.'],
                                  met_list[:2], 
                                  met_list[2:]                          
                                  ], figsize=figsize,
                                 gridspec_kw={'wspace': .25, 'hspace': .4},
                                 per_subplot_kw={'wr_obs': {'projection': 'windrose'},
                                                 'wr_mod': {'projection': 'windrose'}}
                                 )
    

    # ax['ws'].sharex(ax['tc'])
    # ax['wd'].sharex(ax['rh'])
    wind_rose = {'wr_obs': 'Observed', 'wr_mod': 'Modeled'}

    for param in list(ylabels.keys()):

        (met_all
        .plot(ax=ax[param], y = param + '_obs', legend = False, style='.-k',
              label = labels[0]))
        
        (met_all #RH	SFC_TMP	tc PBLH	WSPD10	WDIR10
        .plot(ax=ax[param], y=param + '_mod', style='.-', color = color, 
              alpha = .7, legend = False, label = labels[1]))
        ax[param].set_ylabel(ylabels[param])
        ax[param].set_xlabel(None)
        ax[param].spines['top'].set_visible(False)
        ax[param].spines['right'].set_visible(False)
        
    ax[met_list[0]].set_title(title, loc='left')
    ax['tc'].legend(fontsize='small')
    
    # Windrose subplots --------------------------------------------------------
    wind_obs = met_all.loc[:, ['ws_obs', 'wd_obs'] ].rename(columns={'ws_obs': 'ws', 'wd_obs': 'wd'})
    wind_obs['type'] = 'wr_obs'

    wind_mod = met_all.loc[:, ['ws_mod', 'wd_mod'] ].rename(columns={'ws_mod': 'ws', 'wd_mod': 'wd'})
    wind_mod['type'] = 'wr_mod'
    combined = pd.concat([wind_obs, wind_mod])
    for key in ['wr_obs', 'wr_mod']:
        plot_windrose(direction_or_df=combined.loc[combined['type'] == key, 'wd'], 
                        var=combined.loc[combined['type'] == key, 'ws'], kind='bar',
                        normed=True,
                        calm_limit=0.1,
                        bins=(0.1, 1, 2, 3, 4, 5),
                        ax=ax[key])
        ax[key].set_title(wind_rose[key], loc='center')

    ax['wr_obs'].legend_.set_visible(False)
    ax['wr_mod'].set_legend(
        title=r"$m \cdot s^{-1}$", bbox_to_anchor=(-0.5, 0.5),
        loc="center right")
    
    # Save Figure
    if savefig is not None:
        format = savefig.split('.')[-1]
        if format not in ['png', 'jpg', 'jpeg', 'pdf', 'svg']:
            raise ValueError("Unsupported file format. Supported formats: png, jpg, jpeg, pdf, svg.")
        else:
            print(f"Saving figure to {savefig} as {format} format")
            fig.savefig(savefig, bbox_inches='tight', format=format)
            plt.show()
    else:
        plt.show()

    
# CMAQ plotting function -------------------------------------------------------
# Created by Alejandro Delgado (2024-06-17), version 0.1
def map(combine: xr.Dataset, stat: str, pol: str,
        set_extent: list, cmap:str, 
        plot_kws: dict = None, 
        map_kws:dict = None, 
        cbar_kwargs:dict = None,
        pathsavefile:str = None,  
        shapefiles: list = None, 
        proj_dom: ccrs.CRS = None) -> plt.Figure:
    
    print("Creating a surface map from CMAQ data (COMBINE) ...")
    
    if proj_dom is None:
        proj_dom = ccrs.PlateCarree()
        print("No projection specified. Using PlateCarree as default.")
    else:
        proj_dom = proj_dom
        
    if plot_kws is None:
        plot_kws = dict(nqv = 5, exag = 10, vmin = 5,
                        vmax = 50, levels = 10, 
                        alpha = .6)
    else:
        plot_kws = {**plot_kws}
    
    if map_kws is None:
        map_kws = {'states':True, 'counties':True, 'return_fig': False,
                   'crs': proj_dom, 'linewidth':1}
    else:
        map_kws = {**map_kws, 'crs': proj_dom}
        
    if cbar_kwargs is None:
        if pol in ['PM2.5', 'pm25', 'PM25', 'pm2.5']:
            cbar_kwargs = {'label': 'PM$_{2.5}$ [$\mu g ~m^{-3}$]\n1st high of 24-hour average',
                        'shrink': 0.7, 'aspect': 20}
        elif pol in ['O3', 'o3', 'Ozone', 'ozone']:
            cbar_kwargs = {'label': 'O$_3$ [$\mu g ~m^{-3}$]\n1st high of MDA8h rolling mean', 
                        'shrink': 0.7, 'aspect': 20}
    else:
        cbar_kwargs = {**cbar_kwargs}

    fig, ax = plt.subplots(subplot_kw={'projection': proj_dom}, dpi=150)
    
    x = combine.longitude#[0, :]
    y = combine.latitude#[:, 0]
    u = ((-combine.WSPD10 * np.sin(np.deg2rad(combine.WDIR10)))
         .isel(z=0).mean(dim='time'))
    v = ((-combine.WSPD10 * np.cos(np.deg2rad(combine.WDIR10)))
         .isel(z=0).mean(dim='time'))

    if stat == '24h' and pol in ['PM2.5', 'pm25', 'PM25', 'pm2.5']:
        print("Calculating 24-hour average for PM2.5 and showing worst day ...")
        base = combine.isel(z=0).PM25_TOT.resample(time='24h').mean().max(dim='time')
    
    elif stat == '8h' and pol in ['O3', 'o3', 'Ozone', 'ozone']:
        print("Calculating MDA8-hour average for O3 and showing worst day ...")
        base = (combine.isel(z=0).O3_UGM3.rolling(time=8, min_periods=8).mean()
                .resample(time='D').max()    # Always max of the day for each location
                .max(dim='time'))            # Worst day in each grid cell
    else:
        raise ValueError("Invalid stat or pol. Supported stat: '24h', '8h' for 'PM25', 'O3', respectively.") 
    
    cplot = (base
            .monet
            .quick_contourf(map_kws=map_kws, 
                            cmap = cmap if cmap else 'viridis',
                            levels=plot_kws.get('levels'),
                            vmin = plot_kws.get('vmin'),
                            vmax=plot_kws.get('vmax'),
                            ax=ax,
                            cbar_kwargs=cbar_kwargs, alpha=plot_kws['alpha'],
                            zorder=2))
    
    ## Ploting  o----->
    nqv, exag = plot_kws['nqv'], plot_kws['exag']
    Q = ax.quiver(x[::nqv, ::nqv], y[::nqv, ::nqv], 
                  u[::nqv, ::nqv]*exag, v[::nqv, ::nqv]*exag,
                  units = 'inches', minshaft = 3,  minlength = 2,
                  alpha = plot_kws['alpha'],
                  zorder=1)

    ax.quiverkey(Q, 0.9, 0.9, 1, r'$1 \frac{m}{s}$', labelpos='E', coordinates='figure')
    ## --------------------

    contour_plot = (base
                    .plot
                    .contour(x='longitude',
                            y='latitude',
                            transform = proj_dom,
                            levels=plot_kws['levels'],
                            ax=ax,
                            color = 'black',
                            vmin = plot_kws.get('vmin'),
                            vmax = plot_kws.get('vmax'),
                            linewidths=0.0))
    # Add contour labels
    ax.clabel(contour_plot, inline=True, fontsize=8, colors='black')

    # Shapefile features
    if shapefiles:
        for shape in shapefiles:
            fname = shape
            shape_feature = cfeature.ShapelyFeature(Reader(fname).geometries(), proj_dom)
            ax.add_feature(shape_feature, lw=.5, 
                           edgecolor = 'black', facecolor='none', alpha=.2, zorder=4)
    else:
        pass
    
    ax.set_extent(set_extent, crs=proj_dom)

    gl = cplot.gridlines(draw_labels=True,  
                        color='gray',
                        alpha = .7,
                        linewidth=0.5, linestyle='--')

    gl.top_labels = False   # Don't show labels on top
    gl.right_labels = False  # Don't show labels on the right side
    gl.xlabel_style = {'size': 10, 'color': '0.2'}
    gl.ylabel_style = {'size': 10, 'color': '0.2'}
    
    # Save Figure
    if pathsavefile is not None:
        format = pathsavefile.split('.')[-1]
        if format not in ['png', 'jpg', 'jpeg', 'pdf', 'svg']:
            raise ValueError("Unsupported file format. Supported formats: png, jpg, jpeg, pdf, svg.")
        else:
            print(f"Saving figure to {pathsavefile} as {format} format")
            fig.savefig(pathsavefile, bbox_inches='tight', format=format)
            plt.show()
    else:
        plt.show()

if __name__ == '__main__':
    print()