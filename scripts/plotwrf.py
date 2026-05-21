# conda activate wrf_env in MacBook Pro
from __future__ import print_function

from netCDF4 import Dataset
import time
import pandas as pd
import numpy as np
from wrf import getvar, ALL_TIMES, extract_vars, ll_to_xy, latlon_coords, cartopy_xlim, cartopy_ylim
from glob import glob
import matplotlib.pyplot as plt
import cartopy.feature as cfeature
import cartopy.crs as ccrs
from cartopy.io.shapereader import natural_earth, Reader
from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter
import xarray as xr

# WRF plotting function -------------------------------------------------------
# Created by Alejandro Delgado (2024-06-18), version 0.1

def read_wrfouts(path_wrfouts: str, pols: list, met: bool = False) -> dict[str, xr.DataArray]:
    print("Reading WRF-Chem outputs ...")
    files = glob(path_wrfouts)
    wrfouts = [Dataset(f) for f in files]
    pols_getvar = ['PSFC','T2','rh2','uvmet10_wspd_wdir']
    polsc = []
    for pol in pols:
        if pol in ['PM2.5', 'pm25', 'PM25', 'pm2.5']:
            print(f"{pol} is selected but is PM2_5_DRY in WRF-Chem outputs.")
            pol  = 'PM2_5_DRY'
            polsc.append(pol)
        elif pol in ['O3', 'Ozone', 'ozone']:
            print(f"{pol} is selected but is o3 in WRF-Chem outputs.")
            pol = 'o3'
            polsc.append(pol)
        if pol in pols_getvar:
            print(f"{pol} is extracted using getvar function.")
        else: 
            print(f"I hope {pol} will be the same in WRF-Chem outputs.")
        polsc.append(pol)
    
    windlist = ['U10', 'V10']
    pols = polsc + windlist
    pols = [pol for pol in pols if pol not in pols_getvar]
    #proj_dom = get_cartopy(wrfin=wrfouts[0])
    start = time.time()
    combine = extract_vars(wrfouts, ALL_TIMES, pols)
    
    if met:
        wind = 'uvmet10_wspd_wdir'
        for pol in pols_getvar:
            
            combine[pol] = getvar(wrfouts, pol, timeidx=ALL_TIMES)
            if pol == wind:
                combine['ws'] = combine[wind].sel(wspd_wdir='wspd')
                combine['wd'] = combine[wind].sel(wspd_wdir='wdir')
        del combine[wind]
    else:
        combine['T2'] = getvar(wrfouts, 'T2', timeidx=ALL_TIMES)
    end = time.time()
    print(f"Time taken to read WRF outputs: {end - start:.2f} seconds")

    return combine, wrfouts

# Function to retrieve variables from WRF-Chem
def station_from_wrf(i: int, stations: pd.DataFrame, ds: dict[str, xr.DataArray],
                     t2: xr.DataArray, pols: list,  met: bool = False, 
                     to_local: bool = True, tz: str = 'UTC') -> pd.DataFrame:
    
    if met:
        ds['tc'] = t2 - 273.15
        
        par_dict = {'date': t2.Time.values, 
                    'code': stations.code.values[i]
                    }
        for par in ['tc', 'rh2', 'ws', 'wd']:
            par_dict[par] = ds[par].sel(south_north=stations.y.values[i],
                                        west_east= stations.x.values[i]).values
        for pol in pols:
            if pol in ['o3', 'no', 'no2', 'so2']:
                par_dict[pol] = ds[pol + '_u'].sel(south_north=stations.y.values[i],
                                                   west_east= stations.x.values[i]).values
            else:
                par_dict[pol] = ds[pol + '_sfc'].sel(south_north=stations.y.values[i],
                                                     west_east= stations.x.values[i]).values
    else:      
        par_dict = {'date': t2.Time.values, 
                    'code': stations.code.values[i]
                    }
        for pol in pols:
            if pol in ['o3', 'no', 'no2', 'so2']:
                par_dict[pol] = ds[pol + '_u'].sel(south_north=stations.y.values[i],
                                                   west_east= stations.x.values[i]).values
            else:
                par_dict[pol] = ds[pol + '_sfc'].sel(south_north=stations.y.values[i],
                                                     west_east= stations.x.values[i]).values        
        
    df = pd.DataFrame(par_dict)
    if to_local:
        df['local_date'] = df['date'].dt.tz_localize('UTC').dt.tz_convert(tz)
    else:
        pass

    return df.sort_values('date').drop_duplicates(subset=['code', 'date'])

def wrf_to_stations(path_wrfouts: str, pols: list, met: bool = False,
                   path_stations: str = None, to_local: bool = False,
                   tz: str = 'UTC') -> pd.DataFrame:
    print("From ppm to ug/m3...o3, no, no2, so2, except CO")
    metlist = ['rh2', 'uvmet10_wspd_wdir']
    windlist = ['U10', 'V10']
    for pol in pols:
        if pol in ['PM2.5', 'pm25', 'PM25', 'pm2.5']:
            idx = pols.index(pol)
            pols[idx] = 'PM2_5_DRY'
        elif pol in ['O3', 'Ozone', 'ozone']:
            idx = pols.index(pol)
            pols[idx] = 'o3'
        
    if met:
        polsc = pols + metlist
        ds, wrfouts = read_wrfouts(path_wrfouts, pols = polsc, met=met)
    else:
        ds, wrfouts = read_wrfouts(path_wrfouts, pols = pols)

    # ds is a {str: xr.DataArray}

    # WRF-Chem gas units in ppmv -----------------------------------------------
    # [ug/m3] = [ppm] * P * M_i / (R * T)
    # R = 8.3143 J/K mol
    # P in Pa
    # T in K
    R = 8.3144598 # J/K mol
    start = time.time()
    psfc = getvar(wrfouts, 'PSFC', timeidx=ALL_TIMES)
    t2   = getvar(wrfouts, 'T2', timeidx=ALL_TIMES)
    
    for pol in pols:
        mw = {'o3': 48.00, 'no': 14 + 16, 'no2': 14 + 2*16, 'so2': 32 + 2*16}
        if pol in mw.keys():
            ds[pol + '_u'] = ds[pol].isel(bottom_top=0) * psfc * mw[pol] / (R * t2)
        else:
            ds[pol + '_sfc'] = ds[pol].isel(bottom_top=0)  
    
    # Extracting values at station locations -----------------------------------
    if path_stations is not None:
        print("Extracting values at station locations ...")
        stations = pd.read_csv(path_stations)
        stations_xy = ll_to_xy(wrfouts, latitude = stations.lat,
                               longitude= stations.lon)
        stations['x'], stations['y'] = stations_xy[0], stations_xy[1]
        # Filter stations inside WRF domain
        filter_dom = (stations['x'] > 0) & (stations['x'] < t2.shape[2]) & (stations['y'] > 0) & (stations['y'] < t2.shape[1])
        stations = stations.loc[filter_dom, ]
        
        st_dict = {}
        df_all = pd.DataFrame()
        for i,c in enumerate(stations.code):
            print(f"Processing station {c} ...")
            st_dict[c] = station_from_wrf(i, stations, ds, 
                                          t2, pols, met=met,
                                          to_local=to_local, 
                                          tz=tz)
            df = st_dict[c]
            df_all = pd.concat([df_all, df], ignore_index=True)
        df_all.reset_index(drop='index', inplace=True)
        
        end = time.time()
        print(f"Time for extracting stations from WRF-Chem: {(end - start)/60:.2f} minutes")
                 
        return df_all
        
    else:
        end = time.time()
        print(f"Time taken to process WRF outputs: {(end - start)/60:.2f} minutes")
        return ds

def map(combine: dict[str: xr.Dataset],  pol: str, stat: str, set_extent: list, 
        cmap:str, plot_kws: dict = None, map_kws:dict = None, 
        cbar_kwargs:dict = None, savefig:str = None, 
        shapefiles: list = None, proj_dom: ccrs.CRS = None) -> plt.Figure:
    
    if proj_dom is None:
        print("No projection specified. Using PlateCarree as default.")
        proj_dom = ccrs.PlateCarree()
        
    if plot_kws is None:
        plot_kws = dict(nqv = 5, exag = 10, vmin = 5, vmax = 50, 
                        levels = 8, alpha = .6)
    else:
        plot_kws = {**plot_kws}
    
    if map_kws is None:
        map_kws = {'states':True, 'counties':True, 'return_fig': False,
                   'crs': proj_dom, 'linewidth':2}
    else:
        map_kws = {**map_kws, 'crs': proj_dom}
        
    if cbar_kwargs is None:
        if pol in ['PM2.5', 'pm25', 'PM25', 'pm2.5']:
            cbar_kwargs = {'label': 'PM$_{2.5}$ [$\mu g ~m^{-3}$]\n1st high of 24-hour average'}
        elif pol in ['O3', 'o3', 'Ozone', 'ozone']:
            cbar_kwargs = {'label': 'O$_3$ [$\mu g ~m^{-3}$]\n1st high of MDA8h rolling mean'}
    else:
        cbar_kwargs = {**cbar_kwargs}

    if stat == '24h' and pol in ['PM2.5', 'pm25', 'PM25', 'pm2.5']:
        print("Calculating 24-hour average for PM2.5 and showing worst day ...")
        base  = (combine['PM2_5_DRY'].isel(bottom_top=0)
                 .sortby('Time').drop_duplicates(dim='Time')      # Sort by time
                 .resample(Time='24h').mean().max(dim='Time')
                 )

    elif stat == '8h' and pol in ['O3', 'o3', 'Ozone', 'ozone']:
        print("Calculating MDA8-hour average for O3 and showing worst day ...")
        print("O3 in WRF-Chem is in ppmv.\nConverting units using 1 ppmv = 1996 ug m^-3 at 25 C and 1 atm.")
        base = ((combine['o3'].isel(bottom_top=0) * 1996)
                .sortby('Time').drop_duplicates(dim='Time')
                .rolling(Time=8, min_periods=8).mean()
                .resample(Time='D').max()    # Always max of the day for each location
                .max(dim='Time'))           # Worst day in each grid cell
    else:
        raise ValueError("Invalid stat or pol. Supported stat: '24h', '8h', supported pol: 'PM25', 'O3'.")
    
    lats, lons = latlon_coords(base)
    u = combine['U10'].mean(dim='Time')
    v = combine['V10'].mean(dim='Time')

    # Creating a surface map figure --------------------------------------------
    fig, ax = plt.subplots(subplot_kw={'projection': proj_dom}, dpi=150)       
    cplot = ax.contourf(lons, lats, base, levels=plot_kws['levels'], 
                        vmin=plot_kws['vmin'], vmax=plot_kws['vmax'],
                        transform=proj_dom, alpha= plot_kws['alpha'], zorder=0,
                        cmap=cmap if cmap else 'viridis'
                        )
    
    ## Ploting  o----->
    nqv, exag = plot_kws['nqv'], plot_kws['exag']
    Q = ax.quiver(lons[::nqv, ::nqv], lats[::nqv, ::nqv], 
                  u[::nqv, ::nqv]*exag, v[::nqv, ::nqv]*exag,
                  units = 'inches', minshaft = 3,  minlength = 2,
                  alpha = plot_kws['alpha'],
                  zorder=1)

    ax.quiverkey(Q, 0.85, 0.85, 1, r'$1 \frac{m}{s}$', labelpos='E', coordinates='figure')
    ## --------------------
    
    contour_plot = (ax.contour(lons, lats, base, 
                               levels=plot_kws['levels'],
                               vmin=plot_kws['vmin'], vmax=plot_kws['vmax'],
                               transform=proj_dom, color='black', linewidths=0.0,
                               cmap = cmap if cmap else 'viridis', alpha=0.7))


    # Add contour labels
    ax.clabel(contour_plot, inline=True, fontsize=10, colors='black')
    cbar = fig.colorbar(cplot, ax=ax, orientation='vertical',
                        pad=0.05, shrink=0.8)
    cbar.set_label(cbar_kwargs['label'], size=9)
    cbar.ax.tick_params(labelsize=10)

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
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.STATES, linestyle=':')

    gl = ax.gridlines(draw_labels=True, color = 'gray', 
                      alpha = .7,
                      linewidth = 0.5, 
                      linestyle = '--', 
                      dms=False, x_inline=False, y_inline=False)

    gl.top_labels = False   # Don't show labels on top
    gl.right_labels = False  # Don't show labels on the right side
    gl.xlabel_style = {'size': 10, 'color': '0.2'}
    gl.ylabel_style = {'size': 10, 'color': '0.2'}
    
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

if __name__ == '__main__':
    print()