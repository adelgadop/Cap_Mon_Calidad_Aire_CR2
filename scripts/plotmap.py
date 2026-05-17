from email.mime import base

import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.io.shapereader import natural_earth, Reader
import matplotlib.pyplot as plt
import xarray as xr
import monet
import monetio as mio
import geopandas as gpd
import typing


# CMAQ plotting function -------------------------------------------------------
# Created by Alejandro Delgado (2024-06-17), version 0.1
def cmaq(combine: xr.Dataset, stat: str, pol: str, set_extent: list, cmap:str, 
         plot_kws: dict = None, map_kws:dict = None, cbar_kwargs:dict = None, 
         savefile:bool = False, pathsavefile:str = None, road_map: bool = False, 
         path_roadmap: str = None, shapefile: bool = False, path_shape: str = None,
         proj_dom: ccrs.CRS = None) -> plt.Figure:
    
    print("Creating a surface map from CMAQ data (COMBINE) ...")
    
    if proj_dom is None:
        proj_dom = ccrs.PlateCarree()
        print("No projection specified. Using PlateCarree as default.")
    else:
        proj_dom = proj_dom
        
    if plot_kws is None:
        plot_kws = dict(nqv = 5, exag = 10, vmin = 5, vmax = 50, levels = 8, alpha = .6)
    else:
        plot_kws = {**plot_kws}
    
    if map_kws is None:
        map_kws = {'states':True, 'counties':True, 'return_fig': False,
                   'crs': proj_dom, 'linewidth':2}
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
        base = combine.sel(z=0).PM25_TOT.resample(time='24h').mean().max(dim='time')
    
    elif stat == 'MDA8h' and pol in ['O3', 'o3', 'Ozone', 'ozone']:
        print("Calculating MDA8-hour average for O3 and showing worst day ...")
        base = (combine.sel(z=0).O3_UGM3.rolling(time=8, min_periods=8).mean()
                .resample(time='D').max()    # Always max of the day for each location
                .max(dim='time'))            # Worst day in each grid cell
    else:
        raise ValueError("Invalid stat or pol. Supported stat: '24h', 'MDA8h', supported pol: 'PM25', 'O3'.") 
    
    cplot = (base
            .monet
            .quick_contourf(map_kws=map_kws, cmap = cmap if cmap else 'viridis',
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

    # Roadmap features
    if road_map:
        fname = path_roadmap #'../data/geo_d02_roads.shp/edges.shp'
        shape_feature = cfeature.ShapelyFeature(Reader(fname).geometries(), proj_dom)
        ax.add_feature(shape_feature, lw=.5, edgecolor = 'black', facecolor='none', alpha=.1, zorder=4)
        ax.set_extent(set_extent, crs=proj_dom)
    else:
        ax.set_extent(set_extent, crs=proj_dom)

    # Plot the shapefile (assuming the shapefile uses latitude/longitude coordinates)
    if shapefile:
        gdf = gpd.read_file(path_shape)
        gdf.plot(ax=cplot, edgecolor='k', facecolor='none', linewidth=.5, 
                 alpha = .2, transform=proj_dom)
    else:
        pass

    gl = cplot.gridlines(draw_labels=True,  
                        color='gray',
                        alpha = .7,
                        linewidth=0.5, linestyle='--')

    gl.top_labels = False   # Don't show labels on top
    gl.right_labels = False  # Don't show labels on the right side
    gl.xlabel_style = {'size': 10, 'color': '0.2'}
    gl.ylabel_style = {'size': 10, 'color': '0.2'}
    
    # Save Figure
    if savefile:
        print(f"Saving figure to {pathsavefile}... as pdf format")
        fig.savefig(pathsavefile, bbox_inches='tight', format='pdf')
        plt.show()
    else:
        plt.show()