# conda activate wrf_env  (in Macbook Pro)
import salem
import matplotlib.pyplot as plt
import geobr
import cartopy.feature as cfeature

# Namelist
fpath = '../namelists/namelist.wps.sp'
fname = '../figs/MunRM07.shp'
g, maps = salem.geogrid_simulator(fpath, 
                                  map_kwargs={'countries':False})

# MASP shapefile
# --------------
masp = salem.read_shapefile(fname).set_crs(epsg=4326)
masp['State'] = 'SP' 
masp = masp.dissolve(by='State')
#rma = geobr.read_metro_area()
#masp = (rma
#        .loc[rma.name_metro == 'RM São Paulo',:]
#        .dissolve(by='name_metro')
#        )
#masp['geometry'] = masp.simplify(tolerance=0.001, preserve_topology=False).simplify_coverage(0.001, simplify_boundary=False)

# Reading a shapefile of São Paulo state
sp = geobr.read_state(code_state='SP', year=2019)

# Plot
# ----
fig, ax = plt.subplots()
maps[0].set_rgb(natural_earth='hr')
maps[0].set_scale_bar()
maps[0].set_text(-49.1, -20.5, 'd01', color = 'k', fontweight = 'bold',   fontsize=10)
maps[0].set_text(-47.3, -22.7, 'd02', color = 'k', fontweight = 'bold',    fontsize=8)
#maps[0].set_text(-47.2, -23.3, 'd03', color = 'k', #fontweight = #                 fontsize=5)

maps[0].set_shapefile(masp, lw=1, color='b',
                      countries = False,
                      oceans = False,
                      zorder = 2)

maps[0].set_shapefile(sp, lw=0.5, color='k',
                      countries = False,
                      oceans = False,
                      zorder = 1)

maps[0].set_text(-49.0,-21.25,'São Paulo state',
                 color = 'k',
                 #fontweight = 'bold',
                 fontsize=7)

maps[0].set_text(-46.7, -23.6,'MASP',
                 color = 'k',
                 #fontweight = 'bold',
                 fontsize=7)

maps[0].visualize(ax=ax)
fig.savefig('../figs/map_domain_sp.png', dpi=300,
            bbox_inches='tight', format='png')
#plt.show()

